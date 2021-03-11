import torch
import torch.nn as nn
import torch.nn.functional as f
import torch.optim as optim

cfg = {
    'vgg11': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg13': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg16': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'vgg19': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}


class VGG(nn.Module):
    def __init__(self, config):
        super(VGG, self).__init__()
        if config['dataset'] == 'cifar10':
            final_out = 10
        if config['dataset'] == 'cifar100':
            final_out = 100
        self.features = self._make_layers(cfg[config['nn_type']])
        self.classifier = nn.Sequential(nn.Linear(7*7*512, 4096),
                                        nn.ReLU(inplace=True),
                                        nn.Linear(4096, 4096),
                                        nn.ReLU(inplace=True),
                                        nn.Linear(4096, final_out),
                                        )
        self.optim = optim.SGD(params=self.parameters(),
                               momentum=0.9, lr=config['lr'], nesterov=True)

    def forward(self, x):
        out = self.features(x)
        out = out.view(out.size(0), -1)
        out = self.classifier(out)
        return out

    def _make_layers(self, cfg):
        layers = []
        in_channels = 3
        for x in cfg:
            if x == 'M':
                layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
            else:
                layers += [nn.Conv2d(in_channels, x, kernel_size=3, padding=1),
                           nn.BatchNorm2d(x),
                           nn.ReLU(inplace=True)]
                in_channels = x
        layers += [nn.AdaptiveAvgPool2d(output_size=(7, 7))]

        return nn.Sequential(*layers)


def test():
    net = VGG('VGG11')
    x = torch.randn(2, 3, 32, 32)
    y = net(x)
    print(y.size())


def get_nn_config(vgg_name):
    w_size_list = list()
    b_size_list = list()
    kernel_size_list = list()
    NN_size_list = list()
    NN_type_list = list()

    NN_size_list.append(3)  # 3개 채널 color

    for cnn_info in cfg[vgg_name]:
        if cnn_info != 'M':
            NN_type_list.append('cnn')
            NN_size_list.append(cnn_info)
            kernel_size_list.append((3, 3))
            b_size_list.append(cnn_info)
            w_size_list.append(
                kernel_size_list[-1][0]*kernel_size_list[-1][1]*b_size_list[-1])

    for fc_info in [4096, 4096, 1000]:
        NN_type_list.append('fc')
        NN_size_list.append(fc_info)
        b_size_list.append(fc_info)
        w_size_list.append(b_size_list[-2]*b_size_list[-1])

    return w_size_list, b_size_list, NN_size_list, NN_type_list, kernel_size_list