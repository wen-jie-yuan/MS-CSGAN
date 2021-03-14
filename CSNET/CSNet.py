import torch
import torch.nn as nn


class MSRB_Block(nn.Module):
    def __init__(self):
        super(MSRB_Block, self).__init__()
        self.conv_3_1 = nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1, bias=True)
        self.conv_3_2 = nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1, bias=True)
        self.conv_5_1 = nn.Conv2d(in_channels=64, out_channels=64, kernel_size=5, stride=1, padding=2, bias=True)
        self.conv_5_2 = nn.Conv2d(in_channels=128, out_channels=128, kernel_size=5, stride=1, padding=2, bias=True)
        self.confusion = nn.Conv2d(in_channels=256, out_channels=64, kernel_size=1, stride=1, padding=0, bias=False)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        identity_data = x
        output_3_1 = self.relu(self.conv_3_1(x))
        output_5_1 = self.relu(self.conv_5_1(x))
        input_2 = torch.cat([output_3_1, output_5_1], 1)
        output_3_2 = self.relu(self.conv_3_2(input_2))
        output_5_2 = self.relu(self.conv_5_2(input_2))
        output = torch.cat([output_3_2, output_5_2], 1)

        output = self.confusion(output)
        output = torch.add(output, identity_data)
        return output


class CSNET(torch.nn.Module):
    def __init__(self, num_channels, base_filter):
        super(CSNET, self).__init__()
        # Use convolutional layers to sample and compress the original image
        self.sample = torch.nn.Sequential(
            nn.Conv2d(in_channels=num_channels, out_channels=base_filter, kernel_size=32, stride=32, padding=0,
                      bias=False)
        )
        # Initial reconstruction
        self.initialization = torch.nn.Sequential(
            nn.ConvTranspose2d(in_channels=base_filter, out_channels=1, kernel_size=32, stride=32, padding=0,
                               bias=False)
        )
        # Feature extraction
        self.getFactor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=64, kernel_size=3, stride=1, padding=1, bias=True),
            nn.ReLU(inplace=True),
        )
        self.residual1 = self.make_layer(MSRB_Block)
        self.residual2 = self.make_layer(MSRB_Block)
        self.residual3 = self.make_layer(MSRB_Block)
        self.residual4 = self.make_layer(MSRB_Block)
        self.residual5 = self.make_layer(MSRB_Block)
        self.residual6 = self.make_layer(MSRB_Block)
        self.residual7 = self.make_layer(MSRB_Block)
        self.residual8 = self.make_layer(MSRB_Block)
        self.out = nn.Sequential(
            nn.Conv2d(in_channels=576, out_channels=64, kernel_size=1, stride=1, padding=0, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=1, kernel_size=3, stride=1, padding=1, bias=False),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        out = self.sample(x)
        outInitial = self.initialization(out)
        out = self.getFactor(outInitial)
        LR = out
        out = self.residual1(out)
        concat1 = out
        out = self.residual2(out)
        concat2 = out
        out = self.residual3(out)
        concat3 = out
        out = self.residual4(out)
        concat4 = out
        out = self.residual5(out)
        concat5 = out
        out = self.residual6(out)
        concat6 = out
        out = self.residual7(out)
        concat7 = out
        out = self.residual8(out)
        concat8 = out
        out = torch.cat([LR, concat1, concat2, concat3, concat4, concat5, concat6, concat7, concat8], 1)
        out = self.out(out) + outInitial
        return out

    def make_layer(self, block):
        layers = []
        layers.append(block())
        return nn.Sequential(*layers)

    def weight_init(self, mean, std):
        for m in self._modules:
            normal_init(self._modules[m], mean, std)


def normal_init(m, mean, std):
    if isinstance(m, nn.ConvTranspose2d) or isinstance(m, nn.Conv2d):
        m.weight.data.normal_(mean, std)
        m.bias.data.zero_()
