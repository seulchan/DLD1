import torch.nn.functional as F
import torch
from torch import einsum

def dice_loss(pred, target, smooth = 1.):
    pred = pred.contiguous()
    target = target.contiguous()    
    intersection = (pred * target).sum(dim=2).sum(dim=2)
    loss = (1 - ((2. * intersection + smooth) / (pred.sum(dim=2).sum(dim=2) + target.sum(dim=2).sum(dim=2) + smooth)))
    return loss.mean()

def g_dice_loss(pred, target, smooth = 1.):
    pc = pred
    tc = target
    w = 1 / ((einsum("bcwh->bc", tc).type(torch.float32) + 1e-10) ** 2) #shape Batch x Classes
    intersection = w * einsum("bcwh,bcwh->bc", pc, tc) #shape Batch x Classes
    union = w * (einsum("bcwh->bc", pc) + einsum("bcwh->bc", tc)) #shape Batch x Classes
    numerator = (einsum("bc->b", intersection) + 1e-10) #shape Batch x Classes
    denominator = (einsum("bc->b", union) + 1e-10) #shape Batch x Classes
    divided = 1 - 2 * (numerator / denominator) #Shape Batch
    loss = divided.mean() #scalar
    return loss

def dice_coeff(pred, target, smooth = 1.):
    pred = pred.contiguous()
    target = target.contiguous()    
    intersection = (pred * target).sum(dim=2).sum(dim=2)
    dice = ((2. * intersection + smooth) / (pred.sum(dim=2).sum(dim=2) + target.sum(dim=2).sum(dim=2) + smooth))
    return dice.mean()

def calc_loss(pred, target, metrics, bce_weight=0.5):
    bce = F.binary_cross_entropy_with_logits(pred, target)
    pred = torch.sigmoid(pred)
    dice = g_dice_loss(pred, target)
    loss = bce * bce_weight + dice * (1 - bce_weight)

    metrics['bce'] += bce.data.cpu().numpy() * target.size(0)
    metrics['dice'] += dice.data.cpu().numpy() * target.size(0)
    metrics['loss'] += loss.data.cpu().numpy() * target.size(0)

    return loss

def print_metrics(metrics, epoch_samples, phase):
    outputs = []
    for k in metrics.keys():
        outputs.append("{}: {:4f}".format(k, metrics[k] / epoch_samples))
    print("{}: {}".format(phase, ", ".join(outputs)))