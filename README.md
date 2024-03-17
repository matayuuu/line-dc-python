# デプロイ手順
```
# 環境変数の設定
PROJECT_ID="matayuuu-line-dc"
CLOUDRUN_SERVICE_ACCOUNT="line-bot"
LOCATION="asia-northeast1"
ARTIFACT_REPO="cloud-run-source-deploy"
BQ_DATASET_ID="linebot-googlecloud-sample"
BQ_TABLE_ID="text_info"
CLOUDRUN_NAME="linebot-googlecloud-sample-python"

LINE_CHANNEL_ACCESS_TOKEN="MdU9GoeX06WTcC/SpCUJtu2O8/eiloGacBUionHzPf6G3AQxcteTmfIll5NTPvMerOi5XCuos407RQs/L+PKqsg2rgfUZZZgShoPHMHyiyoh9BIBMscWTNMlzQFYVIAl07LbFipT896r8XqY/e6NXgdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET="7ac781e70435b98ee5315d076b40a746"
PORT="8080"


# 操作するユーザーでログイン
gcloud auth login

# プロジェクト設定の変更
gcloud config set project $PROJECT_ID

# API の有効化
gcloud services enable --project=$PROJECT_ID run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# 

# サービスアカウント作成
gcloud iam service-accounts create $CLOUDRUN_SERVICE_ACCOUNT

# サービスアカウントへ権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDRUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role=roles/bigquery.dataEditor

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
  --set-env-vars="LINE_CHANNEL_ACCESS_TOKEN"=$LINE_CHANNEL_ACCESS_TOKEN \
  --set-env-vars="LINE_CHANNEL_SECRET"=$LINE_CHANNEL_SECRET \
  --set-env-vars="BQ_DATASET_ID"=$BQ_DATASET_ID \
  --set-env-vars="BQ_TABLE_ID"=$BQ_TABLE_ID

```