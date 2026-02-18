# Git Workflow

## After Publishing a Notebook on Kaggle

```bash
# 1. Mark the notebook as published (rename or move to published/)
# 2. Run the tracker
python update_progress.py

# 3. Commit
git add .
git commit -m "[publish] computer-vision/medium/object-detection-yolov8-custom-dataset"

# 4. Push
git push origin main
```

## Commit Message Format

```
[publish]  <folder>/<difficulty>/<notebook-name>
[dataset]  datasets/<category>/<dataset-name>
[update]   <notebook-name> — description of change
[fix]      <notebook-name> — what was fixed
```

## Examples

```
[publish] computer-vision/easy/cnn-from-scratch-explained-simply
[publish] nlp/medium/bert-fine-tuning-text-classification
[dataset] tabular-datasets/customer-churn-prediction-telecom
[update]  xgboost-hyperparameter-tuning-optuna — added optuna dashboard
[fix]     vision-transformer-vit-from-scratch — fixed GPU memory issue
```
