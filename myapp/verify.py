import os
import joblib
import numpy as np

from myapp.train import extract_features


def verify_user_voice(user_id, audio_path, base_media_path):
    """
    Verify an uploaded voice file against the user's trained Isolation Forest model.

    Args:
        user_id: Django User pk
        audio_path: absolute path to the temporary uploaded audio file
        base_media_path: path to  media/voice_uploads/  (parent of user_<id> dirs)

    Returns:
        dict with keys:
            is_valid (bool)  - True if the voice is accepted
            confidence (float) - raw Isolation Forest decision score (higher = more inlier)
    """
    user_dir = os.path.join(base_media_path, f'user_{user_id}')
    model_path = os.path.join(user_dir, 'model.pkl')

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f'Voice model not found for user {user_id}. '
            'Please re-upload and retrain your voice samples.'
        )

    model = joblib.load(model_path)

    features = extract_features(audio_path).reshape(1, -1)

    prediction = model.predict(features)       # +1 = inlier (valid), -1 = outlier (reject)
    score = model.decision_function(features)[0]  # higher = more inlier

    return {
        'is_valid': bool(prediction[0] == 1),
        'confidence': float(score),
    }