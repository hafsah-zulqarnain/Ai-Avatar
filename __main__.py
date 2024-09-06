import pulumi
from pulumi_gcp import storage, serviceaccount, projects, firestore
import pulumi_gcp as gcp

bucket = storage.Bucket('avatar-ai-app',
    location='US',
    versioning={
        'enabled': True,  
    })


firestore_instance = gcp.firestore.Database(
    "my-firestore-ai-avatar-db",
    project="jetrr-hafsa-zulqarnain-1",
    location_id="asia-east2",  
    type="FIRESTORE_NATIVE",  
)

service_account = serviceaccount.Account('my-service-account',
    account_id='my-service-account',
    display_name='My Service Account')

bucket_iam_member_legacy_bucket_owner = storage.BucketIAMMember(
    'bucket-legacy-bucket-owner',
    bucket=bucket.name,
    role='roles/storage.legacyBucketOwner',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

bucket_iam_member_legacy_object_owner = storage.BucketIAMMember(
    'bucket-legacy-object-owner',
    bucket=bucket.name,
    role='roles/storage.legacyObjectOwner',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

bucket_iam_member_object_admin = storage.BucketIAMMember(
    'bucket-object-admin',
    bucket=bucket.name,
    role='roles/storage.objectAdmin',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

bucket_iam_member_object_creator = storage.BucketIAMMember(
    'bucket-object-creator',
    bucket=bucket.name,
    role='roles/storage.objectCreator',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

bucket_iam_member_object_viewer = storage.BucketIAMMember(
    'bucket-object-viewer',
    bucket=bucket.name,
    role='roles/storage.objectViewer',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

datastore_owner = projects.IAMMember(
    'datastore-owner',
    project="jetrr-hafsa-zulqarnain-1", 
    role='roles/datastore.owner',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

datastore_user = projects.IAMMember(
    'datastore-user',
     project="jetrr-hafsa-zulqarnain-1", 
    role='roles/datastore.user',
    member=service_account.email.apply(lambda email: f'serviceAccount:{email}')
)

service_account_key = serviceaccount.Key('my-service-account-key',
    service_account_id=service_account.name)

pulumi.export('bucket_name', bucket.name)
pulumi.export('firestore_database_id', firestore_instance.name)
pulumi.export('service_account_email', service_account.email)
pulumi.export('service_account_key', service_account_key.private_key.apply(lambda pk: "The private key has been generated. Please handle it securely."))
