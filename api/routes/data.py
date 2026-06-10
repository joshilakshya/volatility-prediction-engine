from fastapi import APIRouter, Query, UploadFile, File
from data.loader import get_data
from data.preprocessor import build_features

router = APIRouter(prefix="/data", tags=["Data"])

@router.get("/fetch")
def fetch_data(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = get_data(ticker, period)
    df = df.reset_index()
    df["Date"] = df["Date"].astype(str)
    return {"rows": len(df), "data": df.to_dict(orient="records")}

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...),
                     ticker: str = Query("^GSPC"),
                     period: str = Query("5y")):
    content = await file.read()
    df = get_data(ticker, period, csv_content=content)
    df = build_features(df)
    df = df.reset_index()
    df["Date"] = df["Date"].astype(str)
    return {"rows": len(df), "data": df.where(df.notna(), None).to_dict(orient="records")}
