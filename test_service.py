from get import get_user_email
import gradio as gr
import requests
import base64
from io import BytesIO
import io
from PIL import Image
import pandas as pd
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from google.cloud import storage
import logging
from image_processing import encode_image
from config2 import API_KEY
from config2 import db
from api_requests import create_avatar, get_job_results, get_job_status
from data_display import generate_results_display
# Set up logging configuration
logging.basicConfig(level=logging.INFO)


def update_controlnet_options(controlnet_option):
    return gr.update(visible=(controlnet_option == "Use ControlNet"))

def update_reactor_options(reactor_option):
    return gr.update(visible=(reactor_option == "Use Reactor"))

def handle_submission(num_generations, prompt, negative_prompt, batch_size, steps, cfg_scale, controlnet_option, controlnet_image, controlnet_module, controlnet_model, controlnet_sampler, reactor_option, source_image, upscaler, scale, face_restorer, restorer_visibility, codeformer_weight, restore_first, gender_source, gender_target, save_to_file, device, mask_face, select_source, upscale_force, selected_model):
    # Define ControlNet options (if any)
    user_email = get_user_email()
    print("Inside handler")
    controlnet_options = {}
    if controlnet_option == "Use ControlNet":
        if controlnet_image:
            try:
                if isinstance(controlnet_image, bytes):
                    controlnet_image_encoded = encode_image(controlnet_image)
                    if controlnet_image_encoded:
                        controlnet_options = {
                            "image": controlnet_image_encoded,
                            "module": controlnet_module or "default_module",
                            "model": controlnet_model or "default_model",
                            "sampler_name": controlnet_sampler or "default_sampler"
                        }
            except Exception as e:
                print(f"Failed to process image: {e}")
    
    
    # Define ReActor options
    reactor_options = {}
    if reactor_option == "Use Reactor":
        reactor_options = {
            "source_image": encode_image(source_image) if source_image else None,
            "upscaler": upscaler or "None",
            "scale": scale or 1.5,
            "face_restorer": face_restorer or "None",
            "restorer_visibility": restorer_visibility,
            "codeformer_weight": codeformer_weight or 0.5,
            "restore_first": restore_first,
            "gender_source": gender_source or "None",
            "gender_target": gender_target or "None",
            "save_to_file": save_to_file,
            "device": device or "CPU",
            "mask_face": mask_face,
            "select_source": select_source,
            "upscale_force": upscale_force
        }

    args_reactor = [
            encode_image(source_image), #0
            reactor_option == "Use Reactor", #1 Enable ReActor
            '0', #2 Comma separated face number(s) from swap-source image
            '0', #3 Comma separated face number(s) for target image (result)
            'inswapper_128.onnx', #4 model path
            face_restorer or 'CodeFormer', #4 Restore Face: None; CodeFormer; GFPGAN
            restorer_visibility or 1, #5 Restore visibility value
            True, #7 Restore face -> Upscale
            upscaler or'4x_NMKD-Superscale-SP_178000_G', #8 Upscaler (type 'None' if doesn't need), see full list here: http://127.0.0.1:7860/sdapi/v1/script-info -> reactor -> sec.8
            1.5, #9 Upscaler scale value
            1, #10 Upscaler visibility (if scale = 1)
            False, #11 Swap in source image
            True, #12 Swap in generated image
            1, #13 Console Log Level (0 - min, 1 - med or 2 - max)
            0, #14 Gender Detection (Source) (0 - No, 1 - Female Only, 2 - Male Only)
            0, #15 Gender Detection (Target) (0 - No, 1 - Female Only, 2 - Male Only)
            False, #16 Save the original image(s) made before swapping
            codeformer_weight or 0.8, #17 CodeFormer Weight (0 = maximum effect, 1 = minimum effect), 0.5 - by default
            False, #18 Source Image Hash Check, True - by default
            False, #19 Target Image Hash Check, False - by default
            device or "CUDA", #20 CPU or CUDA (if you have it), CPU - by defaults
            mask_face or True, #21 Face Mask Correction
            0, #22 Select Source, 0 - Image, 1 - Face Model, 2 - Source Folder
            "elena.safetensors", #23 Filename of the face model (from "models/reactor/faces"), e.g. elena.safetensors
            2, #24 The path to the folder containing source faces images
            None, #25 skip it for API
            False, #26 Randomly select an image from the path
            True, #27 Force Upscale even if no face found
            0.6, #28 Face Detection Threshold
            2, #29 Maximum number of faces to detect (0 is unlimited)
        ]
    payload = {
        'input': {
            'prompt': prompt,
            'n_iter': num_generations,
            'batch_size': batch_size,
            'steps': steps,
            'cfg_scale': cfg_scale,
            'width': 512,
            'height': 512,
            'schedule_type':"Automatic",
            'alwayson_scripts': {
                'controlnet': {
                    'args': [
                        {
                            'enabled': controlnet_option == "Use ControlNet",
                            'image': controlnet_options.get("image"),
                            'module': controlnet_options.get("module","canny"),
                            'model': controlnet_options.get("model","control_sd15_canny [fef5e48e]"),
                            'sampler_name': controlnet_options.get("sampler_name","Euler")
                        }
                    ]
                },
                'reactor': {
                    'args':  args_reactor
                }
            },
            'model': selected_model
        }
    }

    print(f"Payload: {payload}")
    try:
        response_data = create_avatar(payload)
        print("Response: ", response_data)
        job_id = response_data.get("id","Failed to create job")
        job_status = response_data.get("status","Failed to get a status")
        job_data = {
            "job_id": job_id,
            "status": job_status,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "controlnet_options": controlnet_options,
            "model": selected_model,
        }
        user_ref = db.collection('users').document(user_email)


        # Ensure the document exists before updating
        if not user_ref.get().exists:
            user_ref.set({
                'email': user_email,
                'jobs': []  # Initialize with an empty jobs list or any other default structure
            })

        user_ref.update({"jobs": firestore.ArrayUnion([job_data])})
        #db.collection('jobs').document(job_id).set({'status': job_status})
        return job_id
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return "Failed to create job"


def check_and_show_results(job_ids):
    user_email =get_user_email()
    results = []
    statuses = []
    for job_id in job_ids:
        status = get_job_status(job_id,user_email)
        statuses.append(status)
        if status == "COMPLETED":
            result_images = get_job_results(job_id, user_email)
            results.extend(result_images)
        else:
            results.append("https://via.placeholder.com/150")
    status_df = pd.DataFrame({"Job ID": job_ids, "Status": statuses})
    return status_df, results

# Building the Gradio Interface
def get_username():
    return get_user_email()

def create_app():
    
    with gr.Blocks() as app:
        gr.Markdown("# AI Avatar Creation")
        #gr.Markdown(f"Welcome, {user_email}")
        print("Code")
        # results = display_results()
        
        # for result in results:
        #     gr.Markdown(f"## Job ID: {result['job_id']}")
        #     gr.Markdown(f"Status: {result['status']}")
        #     for img in result['images']:
        #         gr.Image(img)
        
        username_button = gr.Button("Show Username")
        username_display = gr.Textbox(label="Username")  # Using Textbox to display the username
        
        username_button.click(
            get_username,
            outputs=username_display
        )
        button = gr.Button("Show Gallery")
        results_df = gr.Dataframe(headers=["Job ID", "Status"], label="Job Status")
        image_gallery = gr.Gallery(label="Images")
        
        button.click(
            generate_results_display,
            outputs=[results_df, image_gallery]
        )

        gr.Markdown("### ControlNet Options")
        controlnet_option = gr.Dropdown(
            choices=["None", "Use ControlNet"],
            label="ControlNet Option",
            value="None"
        )

        with gr.Column(visible=False) as controlnet_options:
            controlnet_image = gr.File(label="Upload ControlNet Image", type="binary")

            controlnet_module = gr.Dropdown(choices=[
                "canny", "depth", "mlsd", "openpose"
            ], label="Select ControlNet Module")
            controlnet_model = gr.Dropdown(choices=[
                "control_sd15_canny [fef5e48e]",
                "control_sd15_depth [fef5e48e]",
                "control_sd15_mlsd [fef5e48e]",
                "control_sd15_openpose[fef5e48e]"
            ], label="Select ControlNet Model")
            controlnet_sampler = gr.Dropdown(choices=[
                "Euler", "Euler LMS", "Heun", "DPM2", "DPM2 a",
                "DPM++ 2S a", "DPM++ 2M", "DPM++ SDE", "DPM fast",
                "DPM adaptive", "LMS Karras", "DPM2 Karras",
                "DPM2 a Karras", "DPM++ 25 a Karras", "DPM++ 2M Karras",
                "DPM++ SDE Karras", "DDIM", "PLMS"
            ], label="Select ControlNet Sampler")

        controlnet_option.change(
            update_controlnet_options,
            inputs=controlnet_option,
            outputs=controlnet_options
        )
        
        gr.Markdown("### Reactor Options")
        reactor_option = gr.Dropdown(
            choices=["None", "Use Reactor"],
            label="Reactor Option",
            value="None"
        )

        with gr.Column(visible=False) as reactor_options:
            source_image = gr.File(label="Source Images", type="binary")
            upscaler = gr.Dropdown(choices=["None", "Real-ESRGAN", "ESRGAN"], label="Upscaler")
            scale = gr.Slider(minimum=1.0, maximum=4.0, step=0.1, value=1.5, label="Scale")
            face_restorer = gr.Dropdown(choices=["None", "CodeFormer", "GFPGAN"], label="Face Restorer")
            restorer_visibility = gr.Checkbox(label="Enable Face Restorer", value=True)
            codeformer_weight = gr.Slider(minimum=0.0, maximum=1.0, step=0.1, value=0.5, label="CodeFormer Weight")
            restore_first = gr.Checkbox(label="Restore Faces First", value=True)
            gender_source = gr.Radio(choices=["Male", "Female", "Other"], label="Source Gender")
            gender_target = gr.Radio(choices=["Male", "Female", "Other"], label="Target Gender")
            save_to_file = gr.Checkbox(label="Save Original Image", value=False)
            device = gr.Dropdown(choices=["CPU", "CUDA"], label="Device")
            mask_face = gr.Checkbox(label="Face Mask Correction", value=True)
            select_source = gr.Dropdown(choices=["Image", "Face Model", "Source Folder"], label="Select Source")
            upscale_force = gr.Checkbox(label="Force Upscale", value=False)

        reactor_option.change(
            update_reactor_options,
            inputs=reactor_option,
            outputs=reactor_options
        )

        gr.Markdown("### Model Selection")
        selected_model = gr.Dropdown(
            choices=["absoluteReality.safetensors", "other_model_1", "other_model_2"],
            label="Select Model",
            value="absoluteReality.safetensors"
        )

        gr.Markdown("### Settings")
        num_generations = gr.Slider(minimum=1, maximum=100, step=1, value=1, label="Number of Generations")
        prompt = gr.Textbox(placeholder="Enter your custom prompt here", label="Custom Prompt")
        negative_prompt = gr.Textbox(placeholder="Enter your negative prompt here", label="Negative Prompt")
        batch_size = gr.Slider(minimum=1, maximum=10, step=1, value=1, label="Batch Size")
        steps = gr.Slider(minimum=20, maximum=50, step=1, value=20, label="Steps")
        cfg_scale = gr.Slider(minimum=1, maximum=30, step=0.1, value=7.5, label="CFG Scale")

        submit_btn = gr.Button("Generate Avatars")
        job_id_outputs = gr.Dataframe(headers=["Job ID"], label="Job IDs", interactive=False)

        global job_ids 
        job_ids= []

        def submit_and_store_job(num_generations, prompt, negative_prompt, batch_size, steps, cfg_scale, controlnet_option, controlnet_image, controlnet_module, controlnet_model, controlnet_sampler, reactor_option, source_image, upscaler, scale, face_restorer, restorer_visibility, codeformer_weight, restore_first, gender_source, gender_target, save_to_file, device, mask_face, select_source, upscale_force, selected_model):
            #global job_ids
            print("handle submission")
            job_id = handle_submission(num_generations, prompt, negative_prompt, batch_size, steps, cfg_scale, controlnet_option, controlnet_image, controlnet_module, controlnet_model, controlnet_sampler, reactor_option, source_image, upscaler, scale, face_restorer, restorer_visibility, codeformer_weight, restore_first, gender_source, gender_target, save_to_file, device, mask_face, select_source, upscale_force, selected_model)
            job_ids.append(job_id)
            return pd.DataFrame({"Job ID": [job_id]})

        print("Tester")
        submit_btn.click(
            submit_and_store_job,
            inputs=[num_generations, prompt, negative_prompt, batch_size, steps, cfg_scale, controlnet_option, controlnet_image, controlnet_module, controlnet_model, controlnet_sampler, reactor_option, source_image, upscaler, scale, face_restorer, restorer_visibility, codeformer_weight, restore_first, gender_source, gender_target, save_to_file, device, mask_face, select_source, upscale_force, selected_model],
            outputs=job_id_outputs
        )

        check_results_btn = gr.Button("Check Results")

        results_df = gr.Dataframe(headers=["Job ID", "Status"], label="Job Status")
        results_display = gr.Gallery(label="Results", elem_id="gallery")  # Use scale instead of style

        check_results_btn.click(
            lambda: check_and_show_results(job_ids),
            outputs=[results_df, results_display]
        )
 
    return app
# app = create_app()g
# app.launch()