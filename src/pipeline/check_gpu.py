import torch
print(torch.__version__)
print(torch.version.cuda)
print("Number of Gpu",torch.cuda.device_count())
print("GPU Name",torch.cuda.get_device_name())