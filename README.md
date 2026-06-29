# Cloud Asset Inventory with Effective Tags to BigQuery Exporter

This script solves a common limitation: standard Cloud Asset Inventory exports to BigQuery do not include **effective tags** (the combination of direct and inherited tags). 

This Python script uses the Asset Inventory Search API (`search_all_resources`) to extract resources along with their effective tags and loads them into a BigQuery table, keeping the data structure intact for easy querying.

## 🚀 Features
- Searches resources at the **Organization** level.
- Extracts basic metadata (`name`, `asset_type`, `location`) and **Effective Tags**.
- Supports automatic pagination for handling large volumes of resources.
- Loads data into BigQuery using a structured schema (with repeated/nested fields for tags).
- Can be run locally or deployed as a **Google Cloud Function** (Gen 2) triggered by HTTP or Cloud Scheduler.

---

## 📋 Prerequisites

1. **Python 3.7+** installed.
2. A Google Cloud project with the following APIs enabled:
   - **Cloud Asset API**
   - **BigQuery API**
3. A Dataset already created in BigQuery.

### 🔑 Required IAM Permissions
The service account or user running the script needs at least the following roles:
- **Cloud Asset Viewer** (`roles/cloudasset.viewer`) at the **Organization level**.
- **BigQuery Data Editor** (`roles/bigquery.dataEditor`) on the destination Dataset.
- **BigQuery Job User** (`roles/bigquery.jobUser`) at the Project level.

---

## ⚙️ Configuration (Environment Variables)

The script is configured using the following environment variables:

| Variable | Description | Required | Default Value |
| :--- | :--- | :---: | :--- |
| `ORGANIZATION_ID` | Your GCP Organization numeric ID. | **Yes** | - |
| `BQ_DATASET_ID` | Name of the destination BigQuery Dataset. | No | `asset_inventory_with_tags` |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID for billing/execution. | No | Auto-detected |

---

## 💻 Local Installation and Execution

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd <repository-directory>
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install google-cloud-asset google-cloud-bigquery google-auth
   ```

3. **Configure your credentials:**
   Ensure you are authenticated with Google Cloud in your terminal:
   ```bash
   gcloud auth application-default login
   ```

4. **Set environment variables and run:**
   ```bash
   export ORGANIZATION_ID="your_organization_id"
   export BQ_DATASET_ID="your_bigquery_dataset"
   
   python your_script_name.py
   ```

---

## ☁️ Deployment to Cloud Functions

You can deploy this script as a Cloud Function to automate the export (for example, triggering it daily using Cloud Scheduler).

```bash
gcloud functions deploy export-assets-tags \
    --gen2 \
    --runtime=python310 \
    --region=us-central1 \
    --source=. \
    --entry-point=export_assets_with_tags \
    --trigger-http \
    --set-env-vars ORGANIZATION_ID="your_organization_id",BQ_DATASET_ID="your_dataset"
```

---

## 🛠️ Customization

By default, the script is configured to export Compute Engine instances (`compute.googleapis.com/Instance`). You can modify the resource type by changing the `asset_types` list inside the code:

```python
asset_types = ["compute.googleapis.com/Instance", "storage.googleapis.com/Bucket"]
```
