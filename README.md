# デプロイ手順
```
# カレントディレクトリの移動
cd line-dc-python


# 環境変数の設定
PROJECT_ID=""
LINE_CHANNEL_ACCESS_TOKEN=""
LINE_CHANNEL_SECRET=""

LOCATION="asia-northeast1"
ARTIFACT_REPO="cloud-run-source-deploy"
BQ_DATASET_NAME="linebot_googlecloud_sample"
BQ_TABLE_NAME="text_info"
CLOUDRUN_SERVICE_ACCOUNT="line-bot"
CLOUDRUN_NAME="linebot-googlecloud-sample-python"
SECRET_NAME_LINE_CHANNEL_ACCESS_TOKEN="line-channel-access-token"
SECRET_NAME_LINE_CHANNEL_SECRET="line-channel-secret"


# 操作するユーザーでログイン
gcloud auth login


# プロジェクト設定の変更
gcloud config set project $PROJECT_ID


# API の有効化
gcloud services enable --project=$PROJECT_ID run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com


# BigQuery データセット作成
bq mk -d --location=$LOCATION $PROJECT_ID:$BQ_DATASET_NAME


# BigQuery テーブル作成
bq mk --t $PROJECT_ID:$BQ_DATASET_NAME.$BQ_TABLE_NAME ./schema.json


# シークレット作成（LINE_CHANNEL_ACCESS_TOKEN）
printf $LINE_CHANNEL_ACCESS_TOKEN | gcloud secrets create $SECRET_NAME_LINE_CHANNEL_ACCESS_TOKEN --data-file=-


# シークレット作成（LINE_CHANNEL_SECRET）
printf $LINE_CHANNEL_SECRET | gcloud secrets create $SECRET_NAME_LINE_CHANNEL_SECRET --data-file=-


# サービスアカウント作成
gcloud iam service-accounts create $CLOUDRUN_SERVICE_ACCOUNT


# サービスアカウントへ権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDRUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role=roles/bigquery.dataEditor


gcloud secrets add-iam-policy-binding $SECRET_NAME_LINE_CHANNEL_ACCESS_TOKEN \
  --member="serviceAccount:$CLOUDRUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"


gcloud secrets add-iam-policy-binding $SECRET_NAME_LINE_CHANNEL_SECRET \
  --member="serviceAccount:$CLOUDRUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"


# Artifacts repositories 作成
gcloud artifacts repositories create $ARTIFACT_REPO \
  --location=$LOCATION \
  --repository-format=Docker \
  --project=$PROJECT_ID


# イメージの作成＆更新
gcloud builds submit --tag $LOCATION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$CLOUDRUN_NAME \
  --project=$PROJECT_ID


# Cloud Run デプロイ
gcloud run deploy $CLOUDRUN_NAME --port=$PORT \
  --image $LOCATION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$CLOUDRUN_NAME \
  --allow-unauthenticated \
  --service-account=$CLOUDRUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
  --region=$LOCATION \
  --project=$PROJECT_ID \
  --set-env-vars="PROJECT_ID"=$PROJECT_ID \
  --set-env-vars="BQ_DATASET_NAME"=$BQ_DATASET_NAME \
  --set-env-vars="BQ_TABLE_NAME"=$BQ_TABLE_NAME \
  --set-secrets="LINE_CHANNEL_ACCESS_TOKEN"=$SECRET_NAME_LINE_CHANNEL_ACCESS_TOKEN:latest \
  --set-secrets="LINE_CHANNEL_SECRET"=$SECRET_NAME_LINE_CHANNEL_SECRET:latest
```