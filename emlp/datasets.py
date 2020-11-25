import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from emlp.equivariant_subspaces import Scalar,Vector,Matrix
from torch.utils.data import Dataset
from oil.utils.utils import export,Named,Expression,FixedNumpySeed
from emlp.groups import SO,O,Trivial,Lorentz


@export
class Inertia(Dataset,metaclass=Named):
    def __init__(self,N=1024,k=5):
        super().__init__()
        self.dim = (1+3)*k
        self.X = torch.randn(N,self.dim)
        self.X[:,:k] = F.softplus(self.X[:,:k]) # Masses
        mi = self.X[:,:k]
        ri = self.X[:,k:].reshape(-1,k,3)
        I = torch.eye(3)
        r2 = (ri**2).sum(-1)[...,None,None]
        inertia = (mi[:,:,None,None]*(r2*I - ri[...,None]*ri[...,None,:])).sum(1)
        self.Y = inertia.reshape(-1,9)
        self.rep_in = k*Scalar+k*Vector
        self.rep_out = Matrix
        self.symmetry = O(3)



    def __getitem__(self,i):
        return (self.X[i],self.Y[i])
    def __len__(self):
        return self.X.shape[0]
    def default_aug_layers(self):
        return nn.Sequential()

@export
class Fr(Dataset,metaclass=Named):
    def __init__(self,N=1024):
        super().__init__()
        self.dim = 2*3
        self.X = torch.randn(N,self.dim)
        ri = self.X.reshape(-1,2,3)
        self.Y = (ri[:,0]**2).sum(-1).sqrt().sin()-.5*(ri[:,1]**2).sum(-1).sqrt()**3
        self.rep_in = 2*Vector
        self.rep_out = Scalar
        self.symmetry = O(3)

    def __getitem__(self,i):
        return (self.X[i],self.Y[i])
    def __len__(self):
        return self.X.shape[0]
    def default_aug_layers(self):
        rotate = lambda x: (torch.from_numpy(self.rep_in.rho(\
            self.symmetry.samples(x.shape[0]))).to(x.device)@x.unsqueeze(-1)).squeeze(-1)
        return nn.Sequential(Expression(rotate))

@export
class ParticleInteraction(Dataset,metaclass=Named):
    """ Electron muon e^4 interaction"""
    def __init__(self,N=1024):
        super().__init__()
        self.dim = 4*4
        self.rep_in = 4*Vector
        self.rep_out = Scalar
        self.X = torch.randn(N,self.dim)
        P = self.X.reshape(N,4,4)
        p1,p2,p3,p4 = P.permute(1,0,2)
        𝜂 = torch.diag(torch.tensor([1.,-1.,-1.,-1.]))
        dot = lambda v1,v2: ((v1@𝜂)*v2).sum(-1)
        Le = (p1[:,:,None]*p3[:,None,:] - (dot(p1,p3)-dot(p1,p1))[:,None,None]*𝜂)
        L𝜇 = ((p2@𝜂)[:,:,None]*(p4@𝜂)[:,None,:] - (dot(p2,p4)-dot(p2,p2))[:,None,None]*𝜂)
        M = 4*(Le*L𝜇).sum(-1).sum(-1)
        self.Y = M
        self.symmetry = Lorentz

    def __getitem__(self,i):
        return (self.X[i],self.Y[i])
    def __len__(self):
        return self.X.shape[0]
    def default_aug_layers(self):
        rotate = lambda x: (torch.from_numpy(self.rep_in.rho(\
            self.symmetry.samples(x.shape[0]))).to(x.device)@x.unsqueeze(-1)).squeeze(-1)
        return nn.Sequential(Expression(rotate))
    