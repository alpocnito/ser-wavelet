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
import src.processing as processing

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


def analyze(indata):
    # reading the parameters configuration file
    params = json.load(open('config/mode_1.json', "r"))
    feat_config = params["feature"]
    feat_config["sample_rate"] = int(params["sample_rate"])
    device = (
        torch.device("cuda")
        if params["model"]["use_gpu"] and torch.cuda.is_available()
        else torch.device("cpu")
    )

    model_name = params["model"]["name"]

    model = choose_model(
        mode=params["mode"],
        model_name=model_name,
        device=device,
        dataset=params["dataset"],
    )

    fold = 4
    sr  = 44100
    sample_rate = params["sample_rate"]
    max_samples = 6 * int(params["sample_rate"])
    audio = indata

    if sample_rate != sr:
        audio = processing.resample_audio(audio=audio, sample_rate=sr, new_sample_rate=sample_rate)
        sr = sample_rate

    data = processing.pad_data(features=[audio], max_frames=max_samples)

    data = torch.cat(data, 0).to(dtype=torch.float32)
    data = data.unsqueeze(1)
    labels = torch.as_tensor([0], dtype=torch.long)

    # print(indata)
    # print(len(indata))
    # exit(1)

    # X_train, y_train = processing.processing(
    #     df=train_df, to_mono=params["to_mono"],
    #     sample_rate=params["sample_rate"], max_samples=max_samples
    # )
    X_train = data
    y_train = labels

    # creating the test dataloader
    dataloader = create_dataloader(
        X=X_train,
        y=y_train,
        feature_config=feat_config,
        wavelet_config=params["wavelet"],
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
                params["model"]["output_path"],
                params["dataset"],
                params["mode"],
                model_name,
                f"{model_name}_fold{fold}.pth",
            )
        )["model_state_dict"]
    )

    model.eval()
    predictions = []

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
    print(analyze(torch.FloatTensor([[1, 0, 1]])))
