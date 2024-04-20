import argparse
import os
import json
import torch
import time
import torch.nn as nn
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from torch.utils.data import DataLoader
from src.utils import read_feature, choose_model
from src.dataset import create_dataloader
from typing import Dict
from src.utils import labels_mapping
from src.processing import processing


LABELS = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}


def num_to_str(num: str) -> str:
    return LABELS[num]


def analyse():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", required=True, help="wave file path."
    )
    args = parser.parse_args()
    file = args.w
    wav_file = os.path.basename(file)

    # reading the parameters configuration file
    params = json.load(open('config/mode_1.json', "r"))

    # parameters defination
    k_fold = None

    if "kfold" in params.keys():
        k_fold = params["kfold"]["num_k"]

    feat_config = params["feature"]
    feat_config["sample_rate"] = int(params["sample_rate"])
    wavelet_config = params["wavelet"]

    feat_path = os.path.join(params["output_path"], params["dataset"])
    device = (
        torch.device("cuda") if params["model"]["use_gpu"] and torch.cuda.is_available() else torch.device("cpu")
    )

    output_path = params["model"]["output_path"]
    model_name = params["model"]["name"]

    model = choose_model(
        mode=params["mode"],
        model_name=model_name,
        device=device,
        dataset=params["dataset"],
    )

    fold = 4

    df = pd.DataFrame()
    label = "neutral"

    row = pd.DataFrame(
        {
            "file": [file],
            "label": [label],
            "wav_file": [wav_file],
        }
    )

    df = pd.concat([df, row], axis=0)
    train_df = df.reset_index(drop=True)
    train_df = labels_mapping(df=train_df, dataset="ravdess")

    max_samples = 6 * int(params["sample_rate"])
    X_train, y_train = processing(
        df=train_df, to_mono=params["to_mono"], sample_rate=params["sample_rate"], max_samples=max_samples
    )

    X_test = X_train
    y_test = y_train

    # creating the test dataloader
    dataloader = create_dataloader(
        X=X_test,
        y=y_test,
        feature_config=feat_config,
        wavelet_config=wavelet_config,
        data_augmentation_config=None,
        num_workers=0,
        mode=params["mode"],
        shuffle=False,
        training=False,
        batch_size=params["model"]["batch_size"],
        data_augment_target=None,
    )

    # loading the trained model parameters
    model.load_state_dict(
        torch.load(
            os.path.join(
                output_path,
                params["dataset"],
                params["mode"],
                model_name,
                f"{model_name}_fold{fold}.pth",
            )
        )["model_state_dict"]
    )

    model.eval()
    predictions = []
    targets = []


    with torch.inference_mode():
        for i, batch in enumerate(dataloader):
            data = batch["features"].to(device)
            data = data.to(dtype=torch.float32)
            output = model(data)

            # prediction = output.argmax(dim=-1, keepdim=True).to(dtype=torch.int)
            prediction = output.detach().cpu().numpy()
            predictions.extend(prediction.tolist())

    ret = {num_to_str(str(i+1).zfill(2)): score for i, score in enumerate(predictions[0])}
    return ret

if __name__ == "__main__":
    print(analyse())