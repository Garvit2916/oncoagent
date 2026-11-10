"""Attention-enhanced U-Net architecture (shared from Pan_Organ project)."""

import torch
import torch.nn as nn


class ChannelAttention(nn.Module):
    """Channel attention module."""
    
    def __init__(self, in_planes, ratio=8):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Conv2d(in_planes, in_planes // ratio, 1, bias=False),
            nn.ReLU(),
            nn.Conv2d(in_planes // ratio, in_planes, 1, bias=False)
        )
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        avg_out = self.fc(self.avg_pool(x))
        max_out = self.fc(self.max_pool(x))
        out = avg_out + max_out
        return self.sigmoid(out)


class SpatialAttention(nn.Module):
    """Spatial attention module."""
    
    def __init__(self, kernel_size=7):
        super(SpatialAttention, self).__init__()
        assert kernel_size in (3, 7), 'kernel size must be 3 or 7'
        padding = 3 if kernel_size == 7 else 1
        self.conv1 = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x = torch.cat([avg_out, max_out], dim=1)
        x = self.conv1(x)
        return self.sigmoid(x)


class DualAttentionGate(nn.Module):
    """Dual attention gate combining channel and spatial attention."""
    
    def __init__(self, channels):
        super(DualAttentionGate, self).__init__()
        self.channels = channels
        self.group_channels = channels // 2
        self.channel_att = ChannelAttention(self.group_channels)
        self.spatial_att = SpatialAttention(kernel_size=7)
    
    def forward(self, x):
        x1, x2 = torch.split(x, self.group_channels, dim=1)
        sa = self.spatial_att(x1)
        x1_out = x1 * sa
        ca = self.channel_att(x2)
        x2_out = x2 * ca
        return torch.cat([x1_out, x2_out], dim=1)


class DoubleConv(nn.Module):
    """Double convolution block."""
    
    def __init__(self, in_channels, out_channels, dropout_prob=0.2):
        super(DoubleConv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout2d(p=dropout_prob),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout2d(p=dropout_prob)
        )
    
    def forward(self, x):
        return self.conv(x)


class AttentionEnhancedUNet(nn.Module):
    """Attention-enhanced U-Net for tumor segmentation."""
    
    def __init__(self, in_channels=1, out_channels=1):
        super(AttentionEnhancedUNet, self).__init__()
        self.inc = DoubleConv(in_channels, 16)
        self.down1 = nn.MaxPool2d(2)
        self.conv1 = DoubleConv(16, 32)
        self.down2 = nn.MaxPool2d(2)
        self.conv2 = DoubleConv(32, 64)
        self.down3 = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(64, 128)
        
        self.up1 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.att1 = DualAttentionGate(64)
        self.conv_up1 = DoubleConv(192, 64)
        
        self.up2 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.att2 = DualAttentionGate(32)
        self.conv_up2 = DoubleConv(96, 32)
        
        self.up3 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.att3 = DualAttentionGate(16)
        self.conv_up3 = DoubleConv(48, 16)
        
        self.outc = nn.Conv2d(16, out_channels, 1)
    
    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.conv1(self.down1(x1))
        x3 = self.conv2(self.down2(x2))
        x4 = self.bottleneck(self.down3(x3))
        
        xu1 = self.up1(x4)
        x3_att = self.att1(x3)
        x_dec1 = self.conv_up1(torch.cat([xu1, x3_att], dim=1))
        
        xu2 = self.up2(x_dec1)
        x2_att = self.att2(x2)
        x_dec2 = self.conv_up2(torch.cat([xu2, x2_att], dim=1))
        
        xu3 = self.up3(x_dec2)
        x1_att = self.att3(x1)
        x_dec3 = self.conv_up3(torch.cat([xu3, x1_att], dim=1))
        
        logits = self.outc(x_dec3)
        return logits