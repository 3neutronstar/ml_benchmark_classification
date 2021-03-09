import torch
from torch.utils.tensorboard import SummaryWriter
import matplotlib.pyplot as plt
import csv
import os
import numpy as np
from utils import load_params
def load_csv(configs):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file=open(os.path.join(current_path,'grad_data','grad.csv'),mode='r')
    csvReader=csv.reader(file)
    return csvReader

def visualization(configs):
    csvReader=load_csv(configs)
    CALL_CONFIG=load_params(configs,configs['file_name'])

    if CALL_CONFIG['NN_type']=='lenet5':
        from NeuralNet.lenet5 import w_size_list,b_size_list,NN_size_list,NN_type_list,kernel_size

    grad_data=list()
    weight_data=list()

    # Structure
    # time layer element
    # grad_data = weight ,bias 순서의 layer별 데이터
    # weight_data=weight의 time list, layer list, element tensor
    # data read

    # sum of grad in all node 구조 만들기 (node에서의 elem들의 sum)
    sum_grad_w_node_list=[[[[]for _ in range(CALL_CONFIG['epochs'])] for _ in range(NN_size_list[i+1])] for i,w_size in enumerate(w_size_list)]
    # avg of grad in all node 구조 만들기 (node에서의 elem들의 평균 grad)
    avg_grad_w_node_list=[[[[]for _ in range(CALL_CONFIG['epochs'])] for _ in range(NN_size_list[i+1])] for i,w_size in enumerate(w_size_list)]
    dist_grad_w_node_list=[[[[]for _ in range(CALL_CONFIG['epochs'])] for _ in range(NN_size_list[i+1])] for i,w_size in enumerate(w_size_list)]

    for t,line in enumerate(csvReader):
        line_float=list(map(float,line))
        grad_data.append(list())
        weight_data.append(list())
        for j,(num_w,num_b) in enumerate(zip(w_size_list,b_size_list)):
            tmp_w=torch.tensor(line_float[:num_w])
            line_float=line_float[num_w:]
            grad_data[-1].append(tmp_w)
            weight_data[-1].append(tmp_w)

            if NN_type_list[j]=='cnn':
                for i in range(NN_size_list[j+1]):
                    sum_grad=torch.tensor(tmp_w[:(kernel_size**2)*NN_size_list[j]]).sum().clone().detach().item()
                    dist_grad_w_node_list[j][i]=tmp_w[:(kernel_size**2)*NN_size_list[j]]
                    sum_grad_w_node_list[j][i][t]=sum_grad
                    avg_grad_w_node_list[j][i][t]=sum_grad/float(NN_size_list[j+1])
                    tmp_w =tmp_w[(kernel_size**2)*NN_size_list[j]:]

            elif NN_type_list[j]=='fc':
                for i in range(NN_size_list[j+1]):
                    sum_grad=torch.tensor(tmp_w[:NN_size_list[j]]).sum().clone().detach().item()
                    dist_grad_w_node_list[j][i]=tmp_w[:(kernel_size**2)*NN_size_list[j]]
                    sum_grad_w_node_list[j][i][t]=sum_grad
                    avg_grad_w_node_list[j][i][t]=sum_grad/float(NN_size_list[j+1])
                    tmp_w= tmp_w[NN_size_list[j]:]


            tmp_b=torch.tensor(line_float[:num_b])
            line_float=line_float[num_b:]
            grad_data[-1].append(tmp_b)

    #1 Box plot for checking distribution
    box_w=[list() for i in weight_data[0]]
    for i, node_w in enumerate(weight_data):
        for j,elem_w in enumerate(node_w):
            box_w[j].append(elem_w.tolist())
    for j,_ in enumerate(w_size_list):
        plt.figure(figsize=(40,5))
        plt.boxplot(box_w[j],labels=['{}'.format(k) for k,_ in enumerate(weight_data)],showmeans=True,autorange=True,whis=2)# median 도 표시를 해주자
        plt.title('layer_grad_weight_distribution')
        plt.axis([-0.5,50.5,-0.3,0.3])
        plt.xlabel('epoch')
        plt.savefig('./drive/MyDrive/grad_data/layer_grad_dist/layer_grad_dist_{}.png'.format(j), dpi=200)
    
    # 모든 element에 대해서 time기반 비교
    time_list=list()
    for t,_ in enumerate(weight_data):
        time_list.append(t)

    # 시간에 대해서 저장
    # layer elem time 순 -> elem_w_list
    elem_w_list=[[list() for _ in w] for w in weight_data[0]]# 뒤에 시간별로 더하면됨

    for t,w in enumerate(weight_data):# 모든 시간 t에 대해서
        for j,w_layer in enumerate(w):# 각 layer에 대해서
            for i,elem_w in enumerate(w_layer): #layer내에 대해서
                elem_w_list[j][i].append(elem_w)
    '''
    element 수준에서는 관찰하지 않음
    #2 elem_w_list의 size: layer,weight_i
    # plot and save
    for j,w_node in enumerate(elem_w_list):
        for i,w_elem in enumerate(w_node):
            plt.clf()#clear figure
            plt.plot(time_list,w_elem)
            plt.title('layer{}_elem{}'.format(j,i))
            plt.xlabel('time(epoch)')
            plt.ylabel('sum_of_grad in all elem')
            plt.savefig('./drive/MyDrive/grad_data/layer_node_individ/layer{}_elem{}.png'.format(j,i),dpi=100,facecolor='#eeeeee')
        print(j,'layer done')
    '''
    
    #time 기반 layer별로 gradient 값을 모두 합쳐서 비교
    #sum_w
    # layer,time,weight_sum(elem들의 float)
    sum_w=[[list() for i in range(CALL_CONFIG['epochs'])] for w in elem_w_list] # layer내의/ 시간에 대한/ grad 요소들의 합
    for i,layer_w in enumerate(elem_w_list):# layer구분
        for elem_w in layer_w:# time값을 갖는 elem
            for t,elem_w in enumerate(elem_w): # 각 time 의 elem
                sum_w[i][t]=0.0
    for i,layer_w in enumerate(elem_w_list):# layer구분
        for elem_w in layer_w:# time값을 갖는 elem
            for t,elem in enumerate(elem_w): # 각 time 의 elem
                sum_w[i][t]+=elem.item()/float(w_size_list[i])#averaging
    
    color_list=['red','yellow','green','blue','black']
    plt.figure()
    for j,(w,color) in enumerate(zip(sum_w,color_list)):
        plt.plot(time_list,np.log(w),color=color) # log or not
    plt.title('all_layer_all_node'.format(j))
    plt.xlabel('time(epoch)')
    plt.ylabel('average of grad(by num of elem)')
    plt.legend(['l0','l1','l2','l3','l4'])
    plt.savefig('./drive/MyDrive/grad_data/all_node_all_layer.png',dpi=200,facecolor='#eeeeee')
    
    # 모든 변화량 (x축), element of weight
    # y축은 모든 시간에 대한 gradient의 합
    # layer별로 다르게 분할
    sum_grad_in_time=[[list() for i in w] for w in elem_w_list]
    sum_grad_in_layer_n_time=list()
    for i,layer_w in enumerate(elem_w_list):# layer구분
        for j,elem_w in enumerate(layer_w):# time값을 갖는 elem
            sum_grad=torch.tensor(elem_w).sum().item()# 모든 시간에 대한 합
            sum_grad_in_time[i][j]=sum_grad
        sum_grad_in_layer_n_time.append(torch.tensor(sum_grad_in_time[i]).mean())
    
    #4 모든 layer에 대해서 각 elem(x) 시간에 따른 변화량의 합(y)
    num_node_list=[len(w) for w in elem_w_list]
    for i,(num_node,sum_grad_time) in enumerate(zip(num_node_list,sum_grad_in_time)):
        x_axis=[i for i in range(num_node)]
        plt.clf()#clear figure
        plt.scatter(x_axis,sum_grad_time)
        plt.title('{}_layer_all_node'.format(i))
        plt.xlabel('element_num')
        plt.ylabel('sum of grad in all the times')
        plt.savefig('./grad_data/{}_layer_all_node.png'.format(i),dpi=200,facecolor='#eeeeee')
    #5 모든 layer(x)에서 (모든 시간과 (elem의 평균))(y)
    x_axis=[i for i,_ in enumerate(w_size_list)]
    plt.clf()#clear figure
    plt.scatter(x_axis,sum_grad_in_layer_n_time)
    plt.title('sum of all elem in each layer'.format(i))
    plt.xlabel('layer')
    plt.ylabel('sum of gradient of all elems in all the times')
    plt.savefig('./grad_data/each_layer_all_node.png'.format(i),dpi=200,facecolor='#eeeeee')
            



    print("Visualization")