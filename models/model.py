import torch
import torch.nn as nn
import numpy as np
from torch.autograd import Variable


num_example = 2
batch_size = 3

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.encoder1 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(3, 3))
        self.activation1 = nn.ReLU()
        # self.maxpool1 = nn.MaxPool2d(kernel_size=(2, 2))
        self.encoder2 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(3, 2))
        self.activation2 = nn.ReLU()
        self.encoder3 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=(2, 3))
        self.activation3 = nn.ReLU()
        self.maxpool_over_ino = nn.MaxPool2d(kernel_size=(num_example, 1))

    def forward(self, images):
        encoded = []
        for image in images:
            out = self.encoder1(image)
            out = self.activation1(out)
            out = self.encoder2(out)
            out = self.activation2(out)
            out = self.encoder3(out)
            out = self.activation3(out)
            print(out.shape)
            out = out.view(1, out.size()[0], -1)
            print(out.shape)
            encoded.append(out)
        encoded = torch.cat(tuple(encoded), dim=0)
        encoded = encoded.view(encoded.size()[1], encoded.size()[0], encoded.size()[2])
        encoded = self.maxpool_over_ino(encoded).squeeze()
        print(encoded.shape)



if __name__ == '__main__':
    arr = np.random.uniform(size=(num_example, batch_size, 1, 8, 8))
    model = Model()
    inp = Variable(torch.Tensor(arr))
    out = model(inp)
    # print(out[0].size(), out[1].size())

