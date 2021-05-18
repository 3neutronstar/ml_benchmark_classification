import time
import os
import time
import numpy as np
import torch
from Learner.base_learner import BaseLearner
from CustomOptimizer.layerbylayer import LayerByLayerOptimizer
import sys

class LBLLearner(BaseLearner):
    def __init__(self, model, time_data,file_path, configs):
        super(LBLLearner,self).__init__(model,time_data,file_path,configs)
        self.optimizer=LayerByLayerOptimizer(self.model,self.optimizer)
        self.criterion=self.criterion.__class__(reduction='none')

    def run(self):
        print("Training {} epochs".format(self.configs['epochs']))

        eval_accuracy, eval_loss = 0.0, 0.0
        train_accuracy, train_loss = 0.0, 0.0
        best_eval_accuracy=0.0
        # Train
        for epoch in range(self.configs['start_epoch'], self.configs['epochs'] + 1):
            train_accuracy, train_loss = self._train(epoch)
            eval_accuracy, eval_loss = self._eval()
            self.scheduler.step()
            loss_dict = {'train': train_loss, 'eval': eval_loss}
            accuracy_dict = {'train': train_accuracy, 'eval': eval_accuracy}
            self.logWriter.add_scalars('loss', loss_dict, epoch)
            self.logWriter.add_scalars('accuracy', accuracy_dict, epoch)

            self.early_stopping(eval_loss, self.model)

            if self.early_stopping.early_stop:
                print("Early stopping")
                break
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            if best_eval_accuracy<eval_accuracy:
                best_eval_accuracy=eval_accuracy
        print("Best Accuracy in evaluation: {:.2f}".format(best_eval_accuracy) )
        configs = self.save_grad(epoch)
        return configs

    def _train(self, epoch):
        tik = time.time()
        self.model.train()  # train모드로 설정
        running_loss = 0.0
        correct = 0
        num_training_data = len(self.train_loader.dataset)
        # defalut is mean of mini-batchsamples, loss type설정
        # loss함수에 softmax 함수가 포함되어있음
        # 몇개씩(batch size) 로더에서 가져올지 정함 #enumerate로 batch_idx표현
        for batch_idx, (data, target) in enumerate(self.train_loader):
            data, target = data.to(self.device), target.to(
                self.device)  # gpu로 올림
            # weight prune #TODO
            # model에서 입력과 출력이 나옴 batch 수만큼 들어가서 batch수만큼 결과가 나옴 (1개 인풋 1개 아웃풋 아님)
            output = self.model.layerbylayer_forward(data)
            loss = self.criterion(output, target)  # 결과와 target을 비교하여 계산
            # get the index of the max log-probability
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            self.optimizer.zero_grad()  # optimizer zero로 초기화
            self.optimizer.backward(loss,target)  # 역전파
            self.optimizer.step()

            running_loss += loss.sum().item()
            if batch_idx % self.log_interval == 0:
                print('\r Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(epoch, batch_idx * len(
                    data), num_training_data, 100.0 * batch_idx / len(self.train_loader), loss.sum().item()), end='')
            if self.configs['log_extraction']=='true':
                sys.stdout.flush()         

        running_loss /= num_training_data
        tok = time.time()
        running_accuracy = 100.0 * correct / float(num_training_data)
        print('\nTrain Loss: {:.6f}'.format(running_loss), 'Learning Time: {:.1f}s'.format(
            tok-tik), 'Accuracy: {}/{} ({:.2f}%)'.format(correct, num_training_data, 100.0*correct/num_training_data))
        return running_accuracy, running_loss

    def _eval(self):
        self.model.eval()
        eval_loss = 0
        correct = 0
        class_correct_dict=dict()
        class_total_dict=dict()
        for i in range(self.configs['num_classes']):
            class_correct_dict[i]=0
            class_total_dict[i]=0
        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model.layerbylayer_forward(data)
                loss = self.criterion(output, target)
                eval_loss += loss.sum().item()
                # get the index of the max log-probability
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                for label in target.unique():
                    # print(label,pred.eq(target.view_as(pred))[target==label].sum().item())
                    class_correct_dict[int(label)]+=pred.eq(target.view_as(pred))[target==int(label)].sum().item()
                    class_total_dict[int(label)]+=(target==label).sum().item()
        for keys in class_correct_dict.keys():
            print('{} class : {}/{} [{:.2f}%]'.format(keys,class_correct_dict[keys],class_total_dict[keys],100.0*class_correct_dict[keys]/class_total_dict[keys]))
        eval_loss = eval_loss / len(self.test_loader.dataset)

        print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.2f}%)\n'.format(
            eval_loss, correct, len(self.test_loader.dataset),
            100.0 * correct / float(len(self.test_loader.dataset))))
        if self.configs['log_extraction']=='true':
            sys.stdout.flush()         
        eval_accuracy = 100.0*correct/float(len(self.test_loader.dataset))

        return eval_accuracy, eval_loss