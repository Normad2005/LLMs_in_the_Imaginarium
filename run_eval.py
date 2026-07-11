import sys
sys.path.append("Exploitation")
from evaluation import eval_pred_file, eval_batch
from get_per_api_accuracy import print_per_api_accuracy

print("Evaluating complex dataset...")
try:
    dataset_complex = eval_pred_file("results/icl/outputs_oracle_15_complex.json")
    eval_batch(dataset_complex)
    print_per_api_accuracy("results/icl/outputs_oracle_15_complex.json", "Oracle Complex")
except Exception as e:
    print(f"Error evaluating complex: {e}")

print("Evaluating simple dataset...")
try:
    dataset_simple = eval_pred_file("results/icl/outputs_oracle_15_simple.json")
    eval_batch(dataset_simple)
    print_per_api_accuracy("results/icl/outputs_oracle_15_simple.json", "Oracle Simple")
except Exception as e:
    print(f"Error evaluating simple: {e}")
