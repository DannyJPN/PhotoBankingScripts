#!/usr/bin/env python
"""
Jednoduchý skript pro ověření, že PyTorch byl nainstalován s CUDA podporou.
Spusťte tento skript po instalaci požadavků pro kontrolu CUDA podpory.
"""
import sys

import torch


def check_cuda():
    """Zkontroluje, zda je PyTorch nainstalován s CUDA podporou."""
    print(f"PyTorch verze: {torch.__version__}")

    cuda_available = torch.cuda.is_available()
    print(f"CUDA je dostupná: {cuda_available}")

    if hasattr(torch, "version") and hasattr(torch.version, "cuda"):
        print(f"CUDA verze v PyTorch: {torch.version.cuda}")
    else:
        print("PyTorch byl pravděpodobně nainstalován bez podpory CUDA")

    if cuda_available:
        print(f"Počet CUDA zařízení: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  Zařízení {i}: {torch.cuda.get_device_name(i)}")

        # Zkusíme vytvořit tensor na GPU
        try:
            device = torch.device("cuda")
            test_tensor = torch.zeros(1).to(device)
            print(f"Test tensor vytvořen na: {test_tensor.device}")
            print("CUDA funguje správně!")
            return True
        except Exception as e:
            print(f"Chyba při vytváření tensoru na GPU: {e}")
            return False
    else:
        print("\nPro instalaci PyTorch s CUDA podporou použijte:")
        print("pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118")
        print("\nPokud máte NVIDIA GPU a CUDA stále není dostupná, zkontrolujte:")
        print("1. Máte nainstalované aktuální NVIDIA ovladače")
        print("2. Máte nainstalovaný CUDA Toolkit (není nutné, ale může pomoci)")
        print("3. PyTorch byl nainstalován s podporou CUDA")
        return False


if __name__ == "__main__":
    print("Kontrola CUDA podpory v PyTorch...")
    success = check_cuda()
    sys.exit(0 if success else 1)
