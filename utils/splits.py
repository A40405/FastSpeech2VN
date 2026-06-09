def get_split_filename(train_config, split_name):
    dataset_config = train_config.get("dataset", {})
    default_filenames = {
        "train": "train.txt",
        "val": "val.txt",
    }
    return dataset_config.get(f"{split_name}_file", default_filenames[split_name])
