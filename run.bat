@echo off
echo === Finn. Early Default Prediction Setup ===
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
streamlit run app/main.py
