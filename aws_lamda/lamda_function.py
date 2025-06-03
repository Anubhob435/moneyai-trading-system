import boto3
import csv
import io
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"📥 Received event: {event}")

    try:
        if isinstance(event.get("body"), str):
            event = json.loads(event["body"])

        date_str = event.get("date")
        if not date_str:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'date' in request"})}

        year, month, day = date_str.split("-")
        prefix = f"trading-data/{year}/{month.zfill(2)}/{day.zfill(2)}/"
        bucket_name = "moneyai"

        s3 = boto3.client("s3")

        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        file_key = None
        for obj in response.get("Contents", []):
            if obj["Key"].endswith("trades.csv"):
                file_key = obj["Key"]
                break

        if not file_key:
            return {"statusCode": 404, "body": json.dumps({"error": "trades.csv not found in S3"})}

        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        content = obj["Body"].read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        summary = {}
        for row in reader:
            ticker = row["ticker"]
            price = float(row["price"])
            quantity = int(row["quantity"])

            if ticker not in summary:
                summary[ticker] = {"volume": 0, "total_price": 0, "count": 0}

            summary[ticker]["volume"] += quantity
            summary[ticker]["total_price"] += price
            summary[ticker]["count"] += 1

        # Build CSV string for storage
        output_csv = "ticker,volume,average_price\n"
        for ticker, data in summary.items():
            avg_price = data["total_price"] / data["count"]
            output_csv += f"{ticker},{data['volume']},{round(avg_price, 2)}\n"

        output_key = f"{prefix}analysis_{day}.csv"
        s3.put_object(Bucket=bucket_name, Key=output_key, Body=output_csv)

        logger.info(f"✅ Analysis saved to S3: {output_key}")

        # Build a summary dictionary with final values
        result = {
            ticker: {
                "volume": data["volume"],
                "average_price": round(data["total_price"] / data["count"], 2)
            }
            for ticker, data in summary.items()
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": f"Analysis completed and saved to {output_key}",
                "output_key": output_key,
                "summary": result
            })
        }

    except Exception as e:
        logger.error(f"🔥 Exception occurred: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
