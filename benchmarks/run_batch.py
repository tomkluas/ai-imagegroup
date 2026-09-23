from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import psutil

from image_group.photos.io import ImageLoader
from image_group.recognition.opencv_backend import OpenCvRecognitionBackend
from image_group.tasks.scanner import PhotoScanner


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--input",required=True);parser.add_argument("--models",default="resources/models");parser.add_argument("--json",required=True);args=parser.parse_args()
    scan_start=time.perf_counter();scan=PhotoScanner().scan([Path(args.input)]);scan_seconds=time.perf_counter()-scan_start
    backend=OpenCvRecognitionBackend(Path(args.models));loader=ImageLoader();times=[];faces=0
    for photo in scan.photos:
        started=time.perf_counter();loaded=loader.analysis_image(photo.path,1280);faces+=len(backend.detect_and_embed(loaded.image));times.append(time.perf_counter()-started)
    result={"platform":platform.platform(),"cpu_count":psutil.cpu_count(),"memory_gb":round(psutil.virtual_memory().total/1024**3,2),"photos":len(scan.photos),"faces":faces,"scan_seconds":scan_seconds,"recognition_seconds":sum(times),"errors":len(scan.errors)}
    Path(args.json).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()

