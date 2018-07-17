def get_vocab_map(ckan):
    vocab_map = {}
    for vocab in ckan.action.vocabulary_list():
        vocab_map[vocab['name']] = vocab['id']
    return vocab_map
