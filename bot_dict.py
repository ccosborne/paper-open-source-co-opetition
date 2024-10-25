# Dictionary of bot lists per repository
# Bots identified by manually inspecting top 100 contributors to repo on GitHub via GitHub Insights

bot_dict = {
    "tensorflow/tensorflow": ["tensorflower-gardener"], # https://github.com/tensorflow/tensorflow/graphs/contributors
    "google/jax":["dependabot[bot]"], # https://github.com/google/jax/graphs/contributors
    "keras-team/keras":["tensorflower-gardener"], # https://github.com/keras-team/keras/graphs/contributors
    "pytorch/pytorch": ["pytorchmergebot", "onnxbot", "facebook-github-bot","pytorch-bot[bot]",
                        "pytorchbot", "pytorchupdatebot", "dependabot[bot]", "CodemodService FBSourceClangFormatLinterBot", 
                        "CodemodService FBSourceGoogleJavaFormatLinterBot", "CodemodService FBSourceBlackLinterBot", "CodemodService Bot", 
                        "CodemodService FBSourceBuckFormatLinterBot", "Pyre Bot Jr"], # https://github.com/pytorch/pytorch/graphs/contributors
    "huggingface/transformers": ["dependabot[bot]"], # https://github.com/huggingface/transformers/graphs/contributors
    "huggingface/diffusers":[""], # https://github.com/huggingface/diffusers/graphs/contributors
    "DeepRec-AI/DeepRec":["tensorflower-gardener"], # https://github.com/DeepRec-AI/DeepRec/graphs/contributors
    "microsoft/LightGBM":["GitHubActionsBot"], # https://github.com/microsoft/LightGBM/graphs/contributors
    "mindspore-ai/mindspore":["it-is-a-robot"], # https://github.com/mindspore-ai/mindspore/graphs/contributors
    "PaddlePaddle/Paddle":[""], # https://github.com/PaddlePaddle/Paddle/graphs/contributors
    "catboost/catboost":["arcadia-devtools","robot-piglet", "robot-yandex-devtools-repo",
                         "yandex-contrib-robot","yndx-workfork","dependabot[bot]",
                         "robot-passport-ci","YandexBuildBot","smart-servant"], # https://github.com/catboost/catboost/graphs/contributors
    "mlflow/mlflow":["mlflow-automation","dependabot[bot]"], # https://github.com/mlflow/mlflow/graphs/contributors
}