import os
from google.cloud import asset_v1
from google.cloud import bigquery
import google.auth
import traceback

def export_assets_with_tags(request):
    """Exports Cloud Asset Inventory resources with effective tags to a BigQuery table."""
    try:
        credentials, project_id = google.auth.default()
        if not project_id:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                 _, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            if not project_id:
                 raise Exception("Could not determine Project ID. Set the GOOGLE_CLOUD_PROJECT environment variable.")

        organization_id = os.getenv('ORGANIZATION_ID')
        if not organization_id:
            return "ERROR: ORGANIZATION_ID environment variable not set.", 500

        bq_dataset_id = os.getenv('BQ_DATASET_ID', 'asset_inventory_with_tags')
        bq_table_id = 'compute_instances_with_tags'

        scope = f"organizations/{organization_id}"
        asset_types = ["compute.googleapis.com/Instance"]

        client = asset_v1.AssetServiceClient(credentials=credentials)
        bq_client = bigquery.Client(project=project_id, credentials=credentials)

        rows_to_insert = []
        page_token = None
        print(f"Searching for assets in scope: {scope}")

        while True:
            response = client.search_all_resources(
                request={
                    "scope": scope,
                    "asset_types": asset_types,
                    "read_mask": {"paths": ["name", "asset_type", "location", "effective_tags"]},
                    "page_token": page_token
                }
            )

            for resource in response.results:
                tags_for_resource = []
                if resource.effective_tags:
                    for eff_tag_detail in resource.effective_tags:
                        if eff_tag_detail.effective_tags:
                            for tag in eff_tag_detail.effective_tags:
                                tags_for_resource.append({
                                    "key": tag.tag_key,
                                    "value": tag.tag_value,
                                    "key_id": tag.tag_key_id,
                                    "value_id": tag.tag_value_id,
                                    "attached_resource": eff_tag_detail.attached_resource
                                })

                rows_to_insert.append({
                    "name": resource.name,
                    "asset_type": resource.asset_type,
                    "location": resource.location,
                    "effective_tags": tags_for_resource
                })

            page_token = response.next_page_token
            if not page_token:
                break

        if rows_to_insert:
            print(f"Found {len(rows_to_insert)} resources. Loading to BigQuery...")
            dataset_ref = bq_client.dataset(bq_dataset_id)
            table_ref = dataset_ref.table(bq_table_id)
            job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("name", "STRING"),
                    bigquery.SchemaField("asset_type", "STRING"),
                    bigquery.SchemaField("location", "STRING"),
                    bigquery.SchemaField("effective_tags", "RECORD", mode="REPEATED", fields=[
                        bigquery.SchemaField("key", "STRING"),
                        bigquery.SchemaField("value", "STRING"),
                        bigquery.SchemaField("key_id", "STRING"),
                        bigquery.SchemaField("value_id", "STRING"),
                        bigquery.SchemaField("attached_resource", "STRING"),
                    ]),
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            job = bq_client.load_table_from_json(
                rows_to_insert,
                table_ref,
                job_config=job_config
            )
            job.result()
            print(f"Successfully loaded {len(rows_to_insert)} rows to {project_id}.{bq_dataset_id}.{bq_table_id}")
        else:
            print("No matching resources found to export.")

        return "Asset search and BigQuery load complete.", 200

    except Exception as e:
        print(f"Error during export: {e}")
        traceback.print_exc()
        return f"Error during export: {e}", 500

if __name__ == '__main__':
    print("Ejecutando localmente...")
    response, status_code = export_assets_with_tags(None)
    print(f"Resultado: {response}, Código: {status_code}")
