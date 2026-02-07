from sentence_transformers import SentenceTransformer

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-mpnet-base-v2')
    return _model

def generate_embeddings(text):
    """Generate embeddings from text string or chunk tuple.

    Args:
        text: Either a plain string or a legacy chunk tuple (index at [4] has content).

    Returns:
        numpy array of embeddings.
    """
    model = _get_model()
    if isinstance(text, (list, tuple)):
        # Legacy chunk format: content is at index 4
        content = text[4]
    else:
        content = text
    return model.encode(content)
