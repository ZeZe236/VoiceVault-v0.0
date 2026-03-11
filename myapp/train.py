import os
import joblib
import librosa
import numpy as np
from sklearn.ensemble import IsolationForest

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.m4a', '.flac', '.webm', '.aac', '.opus'}


def extract_features(file_path):
    """Extract 20-coefficient MFCC mean vector from an audio file."""
    y, sr = librosa.load(file_path, sr=16000, mono=True)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    return np.mean(mfcc.T, axis=0)


def train_user_model(user_id, user_audio_dir):
    """
    Train an Isolation Forest model on all audio samples in user_audio_dir.
    Saves model.pkl into the same directory. Requires >= 3 samples.
    """
    print(f"[VoiceVault] Training model for user {user_id}")
    print(f"[VoiceVault] Audio directory: {user_audio_dir}")

    if not os.path.exists(user_audio_dir):
        raise FileNotFoundError(f"User audio directory does not exist: {user_audio_dir}")

    features = []

    for file in sorted(os.listdir(user_audio_dir)):
        # Skip model file and temporary login attempt files
        if file == 'model.pkl' or file.startswith('login_attempt_'):
            continue
        ext = os.path.splitext(file)[1].lower()
        if ext not in AUDIO_EXTENSIONS:
            continue

        path = os.path.join(user_audio_dir, file)
        print(f"[VoiceVault] Processing: {file}")

        try:
            feat = extract_features(path)
            features.append(feat)
        except Exception as e:
            print(f"[VoiceVault] Skipping {file}: {e}")

    if len(features) < 3:
        raise ValueError(
            f"Need at least 3 valid voice samples to train (found {len(features)}). "
            "Make sure files are valid audio."
        )

    X = np.array(features)
    print(f"[VoiceVault] Training with {len(features)} samples, feature shape: {X.shape}")

    # contamination: expected fraction of outliers (login attempts from wrong users)
    model = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        max_samples='auto',
        random_state=42
    )
    model.fit(X)

    model_path = os.path.join(user_audio_dir, 'model.pkl')
    joblib.dump(model, model_path)
    print(f"[VoiceVault] Model saved: {model_path}")

    return model_path