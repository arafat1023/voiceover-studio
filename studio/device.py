"""Report which device the voice models will run on, and why the GPU isn't used if there is one.

    .venv/bin/python -m studio.device

setup.sh runs this at the end. The device itself is picked in studio.tts.pick_device:
mps (Apple Silicon), else cuda (NVIDIA), else cpu.
"""
import shutil
import subprocess

import torch

from studio.tts import pick_device


def nvidia_driver() -> str | None:
    """The NVIDIA driver version, or None when there is no NVIDIA GPU (or no driver)."""
    if not shutil.which('nvidia-smi'):
        return None
    result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                            capture_output=True, text=True)
    return result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else None


def main() -> None:
    device = pick_device()
    if device == 'mps':
        print('device: mps (Apple Silicon GPU)')
    elif device == 'cuda':
        print(f'device: cuda ({torch.cuda.get_device_name(0)}, PyTorch built for CUDA {torch.version.cuda})')
    else:
        print('device: cpu (works, but a long video takes hours)')
    driver = nvidia_driver()
    if device == 'cpu' and driver:
        print(f'  An NVIDIA GPU is present (driver {driver}), but PyTorch is not using it.')
        if torch.version.cuda is None:
            print('  This PyTorch is the CPU-only build (TORCH_CPU=1). To use the GPU: rm -rf .venv, '
                  'then run ./setup.sh without TORCH_CPU.')
        else:
            print(f'  This PyTorch is built for CUDA {torch.version.cuda}; the driver is probably too old for it '
                  '(CUDA 13 needs driver 580+). Update the driver, or: rm -rf .venv, then run '
                  'TORCH_CUDA=cu126 ./setup.sh (CUDA 12.6 works with drivers from about 525).')


if __name__ == '__main__':
    main()
