import enum
import torch
import torch.nn as nn
import copy
import random
import numpy as np
import matplotlib.pyplot as plt

class PCGrad(): # mtl_v2 only# cpu 안내리기
    def __init__(self, optimizer):
        self._optim = optimizer
        return

    @property
    def optimizer(self):
        return self._optim

    def zero_grad(self):
        '''
        clear the gradient of the parameters
        '''

        return self._optim.zero_grad(set_to_none=True)

    def step(self):
        '''
        update the parameters with the gradient
        '''

        return self._optim.step()

    def pc_backward(self, objectives,labels,epoch=None,batch_idx=None):
        '''
        calculate the gradient of the parameters
        input:
        - objectives: a list of objectives
        '''

        grads, shapes = self._pack_grad(objectives)
        pc_grad = self._project_conflicting(grads, epoch=epoch,batch_idx=batch_idx)
        pc_grad = self._unflatten_grad(pc_grad, shapes[0])
        self._set_grad(pc_grad)
        return

    def _project_conflicting(self, grads, shapes=None,epoch=None,batch_idx=None):
        pc_grad, num_task = copy.deepcopy(grads), len(grads)
        #print_norm_before=list()
        #print_norm_after=list()
        #if batch_idx is not None and batch_idx % 10==0:
        #        for g in pc_grad:
        #            print_norm_before.append(g.norm().cpu().clone())
        # print('before',torch.cat(grads,dim=0).view(num_task,-1).mean(dim=1).norm())

        # 1.
        for g_i in pc_grad:
            random.shuffle(grads)
            for g_j in grads:
                g_i_g_j = torch.dot(g_i, g_j)
                if g_i_g_j < 0:
                    g_i -= (g_i_g_j) * g_j / (g_j.norm()**2)
                    # g_i -= (g_i_g_j) * g_j / torch.matmul(g_j,g_j)

        # 2. 
        # for g_i in pc_grad:
        #     surgery=list()
        #     random.shuffle(grads)
        #     for g_j in grads:
        #         g_i_g_j = torch.dot(g_i, g_j)
        #         if g_i_g_j < 0:
        #             # surgery.append(((g_i_g_j) * g_j / (g_j.norm()**2)).view(1,-1))
        #             # surgery.append(((g_i_g_j) * g_j / (g_j.T*g_j).sum()).view(1,-1))
        #             surgery.append(((g_i_g_j) * g_j / torch.matmul(g_j,g_j)).view(1,-1).clone())
        #     if len(surgery)==0:
        #         continue
        #     else:
        #         g_i-=torch.cat(surgery,dim=0).mean(dim=0)

                    
        #if batch_idx is not None and batch_idx % 10==0:
        #    for g in pc_grad:
        #        print_norm_after.append(g.norm().cpu().clone())
        #    plt.clf()
        #    plt.plot(print_norm_before,print_norm_after,'bo')
        #    plt.xlabel('before')            
        #    plt.ylabel('after')            
        #    plt.title('Grad Norm(batch_size:{})_{}e_{}i'.format(num_task,epoch,batch_idx))
        #    plt.savefig('./grad_data/png/batch_{}/{}e_{}iter.png'.format(num_task,epoch,batch_idx))

        merged_grad = torch.cat(pc_grad,dim=0).view(num_task,-1).mean(dim=0)
        
        return merged_grad

    def _set_grad(self, grads):
        '''
        set the modified gradients to the network
        '''

        idx = 0
        for group in self._optim.param_groups:
            for p in group['params']:
                # if p.grad is None: continue
                p.grad = grads[idx]
                idx += 1
        return

    def _pack_grad(self, objectives):
        '''
        pack the gradient of the parameters of the network for each objective
        
        output:
        - grad: a list of the gradient of the parameters
        - shape: a list of the shape of the parameters
        - has_grad: a list of mask represent whether the parameter has gradient
        '''

        grads, shapes = [], []
        for obj in objectives:
            self._optim.zero_grad(set_to_none=True)
            obj.backward(retain_graph=True)
            grad, shape= self._retrieve_grad()
            grads.append(self._flatten_grad(grad, shape))
            shapes.append(shape)
        return grads, shapes

    def _unflatten_grad(self, grads, shapes):
        unflatten_grad, idx = [], 0
        for shape in shapes:
            length = np.prod(shape)
            unflatten_grad.append(grads[idx:idx + length].view(shape).clone())
            idx += length
        return unflatten_grad

    def _flatten_grad(self, grads, shapes):
        flatten_grad = torch.cat([g.flatten() for g in grads])
        return flatten_grad

    def _retrieve_grad(self):
        '''
        get the gradient of the parameters of the network with specific 
        objective
        
        output:
        - grad: a list of the gradient of the parameters
        - shape: a list of the shape of the parameters
        - has_grad: a list of mask represent whether the parameter has gradient
        '''

        grad, shape = [], []
        for group in self._optim.param_groups:
            for p in group['params']:
                # if p.grad is None: continue
                # tackle the multi-head scenario
                if p.grad is None:
                    shape.append(p.shape)
                    grad.append(torch.zeros_like(p).to(p.device))
                    continue
                shape.append(p.grad.shape)
                grad.append(p.grad.clone())
        return grad, shape

class PCGrad_v2(PCGrad):# cpu 내리기
    def __init__(self,optimizer):
        super(PCGrad_v2,self).__init__(optimizer)
        self.objectives=None
        self.shape=[]
        for group in self._optim.param_groups:
            for p in group['params']:
                self.shape.append(p.shape)
        self.i=0
        self.batch_size=0

    @property
    def optimizer(self):
        return self._optim

    def _retrieve_grad(self):
        '''
        get the gradient of the parameters of the network with specific 
        objective
        
        output:
        - grad: a list of the gradient of the parameters
        - shape: a list of the shape of the parameters
        - has_grad: a list of mask represent whether the parameter has gradient
        '''

        grad=[]
        for group in self._optim.param_groups:
            for p in group['params']:
                # if p.grad is None: continue
                # tackle the multi-head scenario
                if p.grad is None:
                    grad.append(torch.zeros_like(p))
                    continue
                grad.append(p.grad.clone())
        return grad

    def _pack_grad(self, objectives):
        grad_list=list()
        for obj in objectives:
            self._optim.zero_grad(set_to_none=True)
            obj.backward(retain_graph=True)
            grad = self._retrieve_grad()
            grad=self._flatten_grad(grad, self.shape)
            grad_list.append(grad.to('cpu'))
        self.objectives=list()
        return grad_list

    def step(self):
        grad_list=self._pack_grad(self.objectives)
        pc_grad_list=copy.deepcopy(grad_list)
        for i, g_i in enumerate(grad_list):
            random.shuffle(pc_grad_list)
            g_i=g_i.cuda()
            if i==0:
                pc_grad=torch.zeros_like(g_i)
            for g_j in pc_grad_list:
                g_j=g_j.cuda()
                g_i_g_j = torch.dot(g_i, g_j)
                if g_i_g_j < 0:
                    g_i -= (g_i_g_j) * g_j / (g_j.norm()**2)
            pc_grad+=g_i
        
        pc_grad=torch.div(pc_grad,self.batch_size)                        
        pc_grad=self._unflatten_grad(pc_grad, self.shape)
        self._set_grad(pc_grad)
        self._optim.step()
        self.objectives=None
        self.i=0
        return 

    def pc_backward(self, objectives,labels):
        self.objectives=objectives
        self.batch_size=len(labels)
        return
