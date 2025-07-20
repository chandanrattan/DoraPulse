import pandas as pd
from pathlib import Path
import shutil

def save_dora_metrics_to_excel(data: dict, output_path: str = "data/dora_metrics.xlsx"):
    df = pd.DataFrame([data])
    
    # Write to backend/data
    backend_excel_path = Path(output_path)
    backend_excel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(backend_excel_path, index=False)
    

    # Copy to frontend/public/data/
    frontend_excel_path = Path("../../frontend/public/data/dora_metrics.xlsx").resolve()
    frontend_excel_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(backend_excel_path, frontend_excel_path)
