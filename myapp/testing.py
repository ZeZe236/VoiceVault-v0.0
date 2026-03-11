import librosa
import numpy as np

def extract_features(audio_path):
    """
    Extract MFCC features from an audio file
    """
    y, sr = librosa.load(audio_path, sr=None)

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=20
    )

    # Take mean over time axis
    return np.mean(mfcc.T, axis=0)