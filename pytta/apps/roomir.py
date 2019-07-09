#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 15:05:17 2019

@author: mtslazarin
"""

# Importando bibliotecas

import pytta
from pytta.classes._base import ChannelObj, ChannelsList
import numpy as np
import copy as cp
import pickle
import matplotlib.pyplot as plot
from os import getcwd, listdir, mkdir
from os.path import isfile, join, exists
from scipy import io

_takeKinds = {'newpoint': None,
              'noisefloor': None,
              'calibration': None}

# Classe da medição


class MeasurementSetup():

    def __init__(self,
                 name,
                 device,
                 excitationSignals,
                 samplingRate,
                 freqMin,
                 freqMax,
                 inChannels,
                 outChannels,
                 averages,
                 sourcesNumber,
                 receiversNumber,
                 noiseFloorTp,
                 calibrationTp):
        self.name = name
        self.device = device
        self.excitationSignals = excitationSignals
        self.samplingRate = samplingRate
        self.freqMin = freqMin
        self.freqMax = freqMax
        self.inChannels = ChannelsList()
        for chCode, chContents in inChannels.items():
            self.inChannels.append(ChannelObj(num=chContents[0],
                                              name=chContents[1],
                                              code=chCode))
        self.outChannels = ChannelsList()
        for chCode, chContents in outChannels.items():
            self.outChannels.append(ChannelObj(num=chContents[0],
                                               name=chContents[1],
                                               code=chCode))
        self.averages = averages
        self.sourcesNumber = sourcesNumber
        self.receiversNumber = receiversNumber
        self.noiseFloorTp = noiseFloorTp
        self.calibrationTp = calibrationTp
                   
    def exportDict(self):
       expdic = vars(self)           
       return _to_dict(expdic)

##%% Classe do dicionário de dados medidos
        
class Data(object):
    
    def __init__(self,MS):
        self.MS = MS
        self.measuredData = {} # Cria o dicionário vazio que conterá todos os níveis de informação do nosso dia de medição
        self.status = {} # Cria o dicionário vazio que conterá o status de cada ponto de medição
        # Gerando chaves para configurações fonte-receptor
        for ch in self.MS.inChannels:
            sourceCode = ch.code
            for rN in range(1,self.MS.receiversNumber+1):
                self.measuredData[sourceCode+'R'+str(rN)] = {} # Insere as chaves referente as configurações fonte receptor
                self.status[sourceCode+'R'+str(rN)] = {}
                for key in MS.excitationSignals:
                    self.measuredData[sourceCode+'R'+str(rN)][key] = {'binaural':0,'hc':0} # Insere as chaves referentes ao sinal de excitação e tipo de gravação            
                    self.status[sourceCode+'R'+str(rN)][key] = {'binaural':False,'hc':False}
        self.measuredData['noisefloor'] = [] # Cria lista de medições de ruído de fundo
        self.status['noisefloor'] = False
        self.measuredData['calibration'] = {} # Cria dicionário com os canais de entrada da medição
        self.status['calibration'] = {}
        for ch in self.MS.inChannels:
            chN = ch.name
            self.measuredData['calibration'][chN] = [] # Cria uma lista de calibrações para cada canal
            self.status['calibration'][chN] = False
            
    def dummyFill(self):
        # Preenche o dicionário de dados medidos com sinais nulos.
        dummyFill = cp.deepcopy(self.MS.excitationSignals)
#        for key in dummyFill:
        for sourceCode in self.MS.inChannels:
            for rN in range(1,self.MS.receiversNumber+1):
                self.measuredData[sourceCode+'R'+str(rN)] = {} # Insere as chaves referente as configurações fonte receptor
                for key in self.MS.excitationSignals:
                    self.measuredData[sourceCode+'R'+str(rN)][key] = {\
                                      'binaural':\
                                      [pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),2),domain='time',samplingRate=self.MS.samplingRate),
                                      pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),2),domain='time',samplingRate=self.MS.samplingRate),
                                      pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),2),domain='time',samplingRate=self.MS.samplingRate)],
                                       'hc':
                                      [pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),1),domain='time',samplingRate=self.MS.samplingRate),
                                      pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),1),domain='time',samplingRate=self.MS.samplingRate),
                                      pytta.SignalObj(np.random.rand(len(dummyFill[key].timeSignal),1),domain='time',samplingRate=self.MS.samplingRate)]} # Insere as chaves referentes ao sinal de excitação e tipo de gravação
                    self.status[sourceCode+'R'+str(rN)][key] = {'binaural':True,'hc':True} # Insere as chaves referentes ao sinal de excitação e tipo de gravação
        noisefloorstr = 'pytta.SignalObj(np.random.rand(self.MS.noiseFloorTp*self.MS.samplingRate,1),domain="time",samplingRate=self.MS.samplingRate)'
        self.measuredData['noisefloor'] = [[eval(noisefloorstr),eval(noisefloorstr),eval(noisefloorstr)],
                         [eval(noisefloorstr),eval(noisefloorstr),eval(noisefloorstr)]] # Cria lista de medições de ruído de fundo
        self.status['noisefloor'] = True # Cria lista de medições de ruído de fundo
        self.measuredData['calibration'] = {} # Cria dicionário com os canais de entrada da medição
        calibrationstr = 'pytta.SignalObj(np.random.rand(self.MS.calibrationTp*self.MS.samplingRate,1),domain="time",samplingRate=self.MS.samplingRate)'
        for chN in self.MS.inChName:
            self.measuredData['calibration'][chN] = [[eval(calibrationstr),eval(calibrationstr),eval(calibrationstr)],
            [eval(calibrationstr),eval(calibrationstr),eval(calibrationstr)]]# Cria uma lista de calibrações para cada canal
            self.status['calibration'][chN] = True
            
    def getStatus(self):
        statusStr = ''
        cEnd = '\x1b[0m'
        cHeader = '\x1b[1;35;43m'
        cHeader2 = '\x1b[1;30;43m'
        cAll = '\x1b[0;30;46m'
        cTrue = '\x1b[3;30;42m'
        cFalse = '\x1b[3;30;41m'
        
#        cEnd = ''
#        cHeader = ''
#        cHeader2 = ''
#        cAll = ''
#        cTrue = ''
#        cFalse = ''
        
        for key in self.status:
            statusStr = statusStr+cHeader+'            '+key+'            '+cEnd+'\n'
            if key == 'noisefloor':
                if self.status[key]:
                    cNF = cTrue
                else:
                    cNF = cFalse
                statusStr = statusStr+''+cNF+str(self.status[key])+cEnd+'\n'
            elif key == 'calibration':
                for ch in self.status[key]:
                    if self.status[key][ch]:
                        cCal = cTrue
                    else:
                        cCal = cFalse
                    statusStr = statusStr+cAll+ch+':'+cEnd+' '+cCal+str(self.status[key][ch])+cEnd+'\n'
#                statusStr = statusStr+'\n'
            else:
                for sig in self.status[key]:
                    statusStr = statusStr+cHeader2+sig+'\n'+cEnd
                    if self.status[key][sig]['binaural']:
                        cBin = cTrue
                    else:
                        cBin = cFalse
                    if self.status[key][sig]['hc']:
                        cHc = cTrue
                    else:
                        cHc = cFalse
                    statusStr = statusStr+cAll+'binaural:'+cEnd+' '+cBin+str(self.status[key][sig]['binaural'])+cEnd+' '
                    statusStr = statusStr+cAll+'h.c.:'+cEnd+' '+cHc+str(self.status[key][sig]['hc'])+cEnd+'\n'
#                statusStr = statusStr+'\n'
#            statusStr = statusStr+'______________________________\n'
                
        return print(statusStr)
#        return statusStr
    
    def exportDict(self):
       expdic = vars(self)           
       return _to_dict(expdic)
   
##%% Classe das tomadas de medição
class measureTake():
    
    def __init__(self,
                 MS,
                 kind,
                 channelStatus,
                 tempHumid,
                 source=None,
                 receivers=None,
                 excitation=None):
        self.tempHumid = tempHumid
        if self.tempHumid != None:
            self.tempHumid.start()
        self.MS = MS
        self.kind = kind
        self.channelStatus = channelStatus
        self.source = source
        self.receivers = receivers
        self.excitation = excitation
        self._cfg_channels()

    def _cfg_channels(self):
        if self.kind == 'newpoint':
            MS.measurementObjects[excitation]
            self.measurementObject = cp.copy(MS.measurementObjects[excitation])
        if self.kind == 'calibration':
            if self.channelStatus.count(True) != 1:
                raise ValueError('Only one channel per calibration take!')
            self.measurementObject = cp.copy(MS.measurementObjects[kind])
        if self.kind == 'noisefloor':
            self.measurementObject = cp.copy(MS.measurementObjects[kind])
        j = 0
        inChannels = ChannelsList()
#        channelName = []
        for i in self.channelStatus:
            if i:
                inChannels.append(self.MS.measurementObjects[excitation].inChannels[j])
#                channelName.append(self.MS.inChName[j])
            j=j+1
        if kind == 'newpoint':
            self.measurementObject.inChannels = \
                ChannelsList(self.MS.inChannels[self.source])
        self.measurementObject.inChannels = inChannels # Ao redefinir a propriedade inChannelo o PyTTa já reajusta a lista channelName com os nomes antigos + nomes padrão para novos canais
#        self.measurementObject.channelName = channelName # Atribuiu os nomes corretos aos canais selecionados

    def _cfg_measurement_object(self):
        # Criando objetos de medição tipo pytta.PlayRecMeasure e pytta.RecMeasure
        self.measurementObjects = {'varredura' : pytta.generate.measurement('playrec',
                                                        excitation=self.excitationSignals['varredura'],
                                                        samplingRate=self.samplingRate,
                                                        freqMin=self.freqMin,
                                                        freqMax=self.freqMax,
                                                        device=self.device,
                                                        inChannels=self.inChannels,
                                                        inChannels=self.inChannels[0],
                                                        comment='varredura'),
                   'musica' : pytta.generate.measurement('playrec',
                                                        excitation=self.excitationSignals['musica'],
                                                        samplingRate=self.samplingRate,
                                                        freqMin=self.freqMin,
                                                        freqMax=self.freqMax,
                                                        device=self.device,
                                                        inChannels=self.inChannels,
                                                        inChannels=self.inChannels[0],
                                                        comment='musica'),
                   'fala' : pytta.generate.measurement('playrec',
                                                        excitation=self.excitationSignals['fala'],
                                                        samplingRate=self.samplingRate,
                                                        freqMin=self.freqMin,
                                                        freqMax=self.freqMax,
                                                        device=self.device,
                                                        inChannels=self.inChannels,
                                                        inChannels=self.inChannels[0],
                                                        comment='fala'),
                   'noisefloor' : pytta.generate.measurement('rec',
                                                         lengthDomain='time',
                                                         timeLength=self.noiseFloorTp,
                                                         samplingRate=self.samplingRate,
                                                         freqMin=self.freqMin,
                                                         freqMax=self.freqMax,
                                                         device=self.device,
                                                         inChannels=self.inChannels,
                                                         comment='noisefloor'),
                   'calibration' : pytta.generate.measurement('rec',
                                                         lengthDomain='time',
                                                         timeLength=self.calibrationTp,
                                                         samplingRate=self.samplingRate,
                                                         freqMin=self.freqMin,
                                                         freqMax=self.freqMax,
                                                         device=self.device,
                                                         inChannels=self.inChannels,
                                                         comment='calibration')}

    @property
    def MS(self):
        return self._MS

    @MS.setter
    def MS(self, newMS):
        if not isinstance(newMS, newMeasurement):
            raise TypeError('Measurement setup must be a newMeasurement ' +
                            'object.')
        self._MS = newMS

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, newKind):
        if not isinstance(newKind, str):
            raise TypeError('Measurement take Kind must be a string')
        if newKind not in _takeKinds:
            raise ValueError('Measurement take Kind doesn\'t ' +
                             'exist in RoomIR application.')
        self._kind = newKind
        return

    @property
    def channelStatus(self):
        return self._channelStatus

    @channelStatus.setter
    def channelStatus(self, newChStatus):
        if not isinstance(newChStatus, list):
            raise TypeError('channelStatus must be a list of booleans ' +
                            'with same number of itens as '+self.MS.name +
                            '\'s inChannels.')
        if len(newChStatus) < len(self._MS.inChannels):
            raise ValueError('channelStatus\' number of itens must be the ' +
                             'same as ' + self.MS.name + '\'s inChannels.')
        for item in newChStatus:
            if not isinstance(item, bool):
                raise TypeError('channelStatus must be a list of booleans ' +
                                'with the same number of itens as ' +
                                self.MS.name + '\'s inChannels.')
        self._channelStatus = newChStatus

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, newSource):
        if not isinstance(newSource, str):
            if newSource is None and self.kind in ['noisefloor',
                                                   'calibration']:
                self._source = None
                return
            else:
                raise TypeError('Source must be a string.')
        if newSource not in self.MS.outChannels:
            raise ValueError(newSource + ' doesn\'t exist in ' +
                             self.MS.name + '\'s outChannels.')
        self._source = newSource

    @property
    def receivers(self):
        return self._receivers

    @receivers.setter
    def receivers(self, newReceivers):
        if not isinstance(newReceivers, list):
            if newReceivers is None and self.kind in ['noisefloor']:
                self._receivers = None
                return
            else:
                raise TypeError('Receivers must be a list of strings ' +
                                'with same number of transducers and itens ' +
                                ' in ' + self.MS.name + '\'s inChannels ' +
                                '(e.g. [\'R1\', \'R5\', \'R13\'])')
        if len(newReceivers) < len(self._MS.inChannels):
            raise ValueError('Receivers\' number of itens must be the ' +
                             'same as ' + self.MS.name + '\'s inChannels.')
        for item in newReceivers:
            if item.split('R')[0] != '':
                raise ValueError(item + 'isn\'t a receiver position. It ' +
                                 'must start with \'R\' succeeded by It\'s ' +
                                 'number (e.g. R1).')
            else:
                try:
                    receiverNumber = int(item.split('R')[1])
                except ValueError:
                    raise ValueError(item + 'isn\'t a receiver position ' +
                                     'code. It must start with \'R\' ' +
                                     'succeeded by It\'s number (e.g. R1).')
                if receiverNumber > self.MS.receiversNumber:
                    raise TypeError('Receiver number out of ' + self.MS.name +
                                    '\'s receivers range.')
        self._receivers = newReceivers
        return

    @property
    def excitation(self):
        return self._excitation

    @excitation.setter
    def excitation(self, newExcitation):
        if not isinstance(newExcitation, str):
            if newExcitation is None and self.kind in ['noisefloor',
                                                       'calibration']:
                self._excitation = None
                return
            else:
                raise TypeError('Excitation signal\'s name must be a string.')
        if newExcitation not in self.MS.excitationSignals:
            raise ValueError('Excitation signal doesn\'t exist in ' +
                             self.MS.name + '\'s excitationSignals')
        self._excitation = newExcitation
        return

    def run(self):
        self.measuredTake = []
#        if self.kind == 'newpoint':
        for i in range(0,self.MS.averages):
            self.measuredTake.append(self.measurementObject.run())
#            self.measuredTake[i].plot_time()
            # Adquire do LabJack U3 + EI1050 a temperatura e umidade relativa instantânea
            if self.tempHumid != None:
                self.measuredTake[i].temp, self.measuredTake[i].RH = self.tempHumid.read()
            else:
                self.measuredTake[i].temp, self.measuredTake[i].RH = (None,None)
            
    def save(self,dataObj):
        # Desmembra o SignalObj measureTake de 4 canais em 3 SignalObj referentes ao arranjo biauricular 
        # em uma posição e ao centro da cabeça em duas outras posições
        if self.kind == 'newpoint' or self.kind == 'noisefloor':
            chcont = 0
            self.binaural=[]
            self.hc1=[]
            self.hc2=[]
            if self.channelStatus[0] and self.channelStatus[1]:
                for i in range(0,self.MS.averages):
                    self.binaural.append(pytta.SignalObj(self.measuredTake[i].timeSignal[:,chcont:chcont+2],
                                               'time',
                                               samplingRate=self.measuredTake[i].samplingRate,
                                               comment=self.excitation))
                    self.binaural[-1].channels[0].name = self.MS.inChannels[0].name
                    self.binaural[-1].channels[1].name = self.MS.inChannels[1].name
                    if self.kind == 'noisefloor': 
                        SR = [self.receivers[0],self.receivers[1]] 
                    else: 
                        SR = [self.source+self.receivers[0],self.source+self.receivers[1]]
                    self.binaural[i].sourceReceiver = SR
                    self.binaural[i].temp = self.measuredTake[i].temp
                    self.binaural[i].RH = self.measuredTake[i].RH
                    self.binaural[i].timeStamp = self.measuredTake[i].timeStamp
                chcont = chcont + 2
            if self.channelStatus[2]:
                for i in range(0,self.MS.averages):
                    self.hc1.append(pytta.SignalObj(self.measuredTake[i].timeSignal[:,chcont],
                                          'time',
                                          samplingRate=self.measuredTake[i].samplingRate,
                                          comment=self.excitation))
                    self.hc1[-1].channels[0].name = self.MS.inChannels[2].name
                    if self.kind == 'noisefloor': 
                        SR = self.receivers[2]
                    else: 
                        SR = self.source+self.receivers[2]
                    self.hc1[i].sourceReceiver = SR
                    self.hc1[i].temp = self.measuredTake[i].temp
                    self.hc1[i].RH = self.measuredTake[i].RH
                    self.hc1[i].timeStamp = self.measuredTake[i].timeStamp
                chcont = chcont + 1
            if self.channelStatus[3]:
                for i in range(0,self.MS.averages):
                    self.hc2.append(pytta.SignalObj(self.measuredTake[i].timeSignal[:,chcont],
                                          'time',
                                          samplingRate=self.measuredTake[i].samplingRate,
                                          comment=self.excitation))
                    self.hc2[-1].channels[0].name = self.MS.inChannels[3].name
                    if self.kind == 'noisefloor': 
                        SR = self.receivers[3]
                    else: 
                        SR = self.source+self.receivers[3]
                    self.hc2[i].sourceReceiver = SR
                    self.hc2[i].temp = self.measuredTake[i].temp
                    self.hc2[i].RH = self.measuredTake[i].RH
                    self.hc2[i].timeStamp = self.measuredTake[i].timeStamp        

        # Salva dados no dicionário do objeto de dados dataObj
        taketopkl = {'measuredData':{},'status':{}}
        if self.kind == 'newpoint':
            # Adiciona cada uma das três posições de receptor da última tomada de medição     
            if self.channelStatus[0] and self.channelStatus[1]:
                dataObj.measuredData[self.binaural[0].sourceReceiver[0]][self.binaural[0].comment]['binaural'] = self.binaural
                taketopkl['measuredData'][self.binaural[0].sourceReceiver[0]] = {self.binaural[0].comment:{'binaural':self.binaural}}
                dataObj.status[self.binaural[0].sourceReceiver[0]][self.binaural[0].comment]['binaural'] = True
                taketopkl['status'][self.binaural[0].sourceReceiver[0]] = {self.binaural[0].comment:{'binaural': True}}
            if self.channelStatus[2]:
                dataObj.measuredData[self.hc1[0].sourceReceiver][self.hc1[0].comment]['hc'] = self.hc1
                taketopkl['measuredData'][self.hc1[0].sourceReceiver] = {self.hc1[0].comment:{'hc':self.hc1}}
                dataObj.status[self.hc1[0].sourceReceiver][self.hc1[0].comment]['hc'] = True
                taketopkl['status'][self.hc1[0].sourceReceiver] = {self.hc1[0].comment:{'hc':True}}
            if self.channelStatus[3]:
                dataObj.measuredData[self.hc2[0].sourceReceiver][self.hc2[0].comment]['hc'] = self.hc2
                taketopkl['measuredData'][self.hc2[0].sourceReceiver] = {self.hc2[0].comment:{'hc':self.hc2}}
                dataObj.status[self.hc2[0].sourceReceiver][self.hc2[0].comment]['hc'] = True
                taketopkl['status'][self.hc2[0].sourceReceiver] = {self.hc2[0].comment:{'hc':True}}
                
        if self.kind == 'noisefloor':
            newNF = {}
            if self.channelStatus[0] and self.channelStatus[1]:
                newNF[self.binaural[0].sourceReceiver[0]] = self.binaural
            if self.channelStatus[2]:
                newNF[self.hc1[0].sourceReceiver] = self.hc1
            if self.channelStatus[3]:
                newNF[self.hc2[0].sourceReceiver] = self.hc2
            dataObj.measuredData['noisefloor'].append(newNF)
            taketopkl['measuredData']['noisefloor'] = newNF
            dataObj.status['noisefloor'] = True
            taketopkl['status']['noisefloor'] = True
            
        if self.kind == 'calibration':
            self.calibAverages = []
            # Pegando o nome do canal calibrado
            j=0
            for i in self.channelStatus:
                if i:
                    self.inChName = [self.MS.inChName[j]]
                j=j+1
            for i in range(0,self.MS.averages):
                self.calibAverages.append(pytta.SignalObj(self.measuredTake[i].timeSignal[:,0],
                                      'time',
                                      samplingRate=self.measuredTake[i].samplingRate,
#                                      channelName=self.inChName,
                                      comment=self.excitation))
                self.calibAverages[i].channels[0].name = self.MS.inChName[0]
#                self.calibAverages[i].sourceReceiver = self.sourceReceiver[2]
                self.calibAverages[i].temp = self.measuredTake[i].temp
                self.calibAverages[i].RH = self.measuredTake[i].RH
                self.calibAverages[i].timeStamp = self.measuredTake[i].timeStamp
            dataObj.measuredData['calibration'][self.inChName[0]].append(self.calibAverages)
            taketopkl['measuredData']['calibration'] = {self.inChName[0]:self.calibAverages}
            dataObj.status['calibration'][self.inChName[0]] = True
            taketopkl['status']['calibration'] = {self.inChName[0]:True}
        if self.tempHumid != None:
            self.tempHumid.stop()

        # Save last take to file
        mypath = getcwd()+'/'+self.MS.name+'/'
        mytakefilesprefix = self.MS.name+'_D_take-'
        myMSfile = self.MS.name+'_MS'
        if not exists(mypath):
            mkdir(mypath)
        myfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        lasttake = 0
        saveMS = True
        for file in myfiles:
            if mytakefilesprefix in file:
                newlasttake = file.replace(mytakefilesprefix,'')
                newlasttake = int(newlasttake.replace('.pkl',''))
                if newlasttake > lasttake:
                    lasttake = newlasttake
            if myMSfile in file:
                saveMS = False
        if saveMS:
            msD = {'averages':self.MS.averages,
                   'calibrationTp':self.MS.calibrationTp,
                   'device':self.MS.device,
                   'excitationSignals':self.MS.excitationSignals,
                   'freqMax':self.MS.freqMax,
                   'freqMin':self.MS.freqMin,
#                   'inChName':self.MS.inChName,
                   'inChannels':self.MS.inChannels,
#                   'measurementObjects':self.MS.measurementObjects,
                   'name':self.MS.name,
                   'noiseFloorTp':self.MS.noiseFloorTp,
                   'inChannels':self.MS.inChannels,
                   'receiversNumber':self.MS.receiversNumber,
                   'samplingRate':self.MS.samplingRate,
                   'sourcesNumber':self.MS.sourcesNumber}
            output = open(mypath+myMSfile+'.pkl', 'wb')
            pickle.dump(msD,output)
            output.close()
        output = open(mypath+mytakefilesprefix+str(lasttake+1)+'.pkl', 'wb')
        pickle.dump(taketopkl,output)
        output.close()       
        
    def take_check(self):
        if self.measuredTake[0].num_channels() > 1:
            for chIndex in range(self.measuredTake[0].num_channels()):
                plot.figure( figsize=(6,5) )
                label = self.measuredTake[0].channels[chIndex].name+' ['+self.measuredTake[0].channels[chIndex].unit+']'
                plot.plot( self.measuredTake[0].timeVector,self.measuredTake[0].timeSignal[:,chIndex],label=label)
                plot.legend(loc='best')
                plot.grid(color='gray', linestyle='-.', linewidth=0.4)
                plot.axis( ( self.measuredTake[0].timeVector[0] - 10/self.measuredTake[0].samplingRate, \
                            self.measuredTake[0].timeVector[-1] + 10/self.measuredTake[0].samplingRate, \
                            1.05*np.min( self.measuredTake[0].timeSignal ), \
                           1.05*np.max( self.measuredTake[0].timeSignal ) ) )
                plot.xlabel(r'$Time$ [s]')
                plot.ylabel(r'$Amplitude$')
    
def load(medname):
    mypath = getcwd()+'/'+medname+'/'
    mytakefilesprefix = medname+'_D_take-'
    myMSfile = medname+'_MS'
    if not exists(mypath):
        raise NameError(medname+' not find in the current working directory')
    myfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    #Load MS
    pkl_file = open(mypath+myMSfile+'.pkl', 'rb')
    loadDict = pickle.load(pkl_file)
    pkl_file.close()
    MS = newMeasurement(averages = loadDict['averages'],
                        calibrationTp = loadDict['calibrationTp'],
                        device = loadDict['device'],
                        excitationSignals = loadDict['excitationSignals'],
                        freqMax = loadDict['freqMax'],
                        freqMin = loadDict['freqMin'],
                        inChName = loadDict['inChName'],
                        inChannels = loadDict['inChannels'],
                        name = loadDict['name'],
                        noiseFloorTp = loadDict['noiseFloorTp'],
                        inChannels = loadDict['inChannels'],
                        receiversNumber = loadDict['receiversNumber'],
                        samplingRate = loadDict['samplingRate'],
                        sourcesNumber = loadDict['sourcesNumber'])    
    MS.measurementObjects = loadDict['measurementObjects']
    # Load data
    D = Data(MS)
    for file in myfiles:
        if mytakefilesprefix in file:
            pkl_file = open(mypath+file, 'rb')
            loadDict = pickle.load(pkl_file)            
            for key in loadDict:
                if key == 'measuredData':
                    for key, value in loadDict['measuredData'].items():
                        if key == 'calibration':
                            for key2, value2 in loadDict['measuredData'][key].items():
                                D.measuredData[key][key2].append(value2)
                        elif key == 'noisefloor':
                                D.measuredData[key].append(value)
                        else:
                            for key2, value2 in loadDict['measuredData'][key].items():
                                D.measuredData[key][key2] = {**D.measuredData[key][key2],**value2}
                if key == 'status':
                    for key, value in loadDict['status'].items():
                        if key == 'calibration':
                            for key2, value2 in loadDict['status'][key].items():
                                D.status[key][key2] = value2
                        elif key == 'noisefloor':
                                D.status[key] = value
                        else:
                            for key2, value2 in loadDict['status'][key].items():
                                D.status[key][key2] = {**D.status[key][key2],**value2}
    return MS, D

def med_to_mat(medname):
    """Exports all stored measurement .pkl files to .mat files"""
    mypath = getcwd()+'/'+medname+'/'
    mymatpath = getcwd()+'/'+medname+'_mat/'
    if not exists(mymatpath):
        mkdir(mymatpath)
    mytakefilesprefix = medname+'_D_take-'
    myMSfile = medname+'_MS'
    if not exists(mypath):
        raise NameError(medname+' not find in the current working directory')
    myfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    #Load MS
    myMSpklfile = open(mypath+myMSfile+'.pkl', 'rb')
    myMSdict = pickle.load(myMSpklfile)
    myMSpklfile.close()
    myMSdict = _to_dict(myMSdict)
    io.savemat(mymatpath+myMSfile+'.mat',{'MeasurementSetup':myMSdict},format='5')
    for file in myfiles:
        filename = file.replace('.pkl','')
        if mytakefilesprefix in file:
            pkl_file = open(mypath+file, 'rb')
            loadDict = pickle.load(pkl_file)            
            for key in loadDict:
                if key == 'measuredData':
                    print('Exporting "'+filename+'" to .mat file.\n')
                    matDict = _to_dict(loadDict)
                    io.savemat(mymatpath+filename+'.mat',matDict,format='5')


def _to_dict(thing):
    
    # From SignalObj to dict
    if isinstance(thing, SignalObj):
        mySigObj = vars(thing)
        dictime = {}
        for key, value in mySigObj.items():
            # Recursive stuff for values
            dictime[key] = _to_dict(value)
        # Recursive stuff for resultant dict
        return _to_dict(dictime)

    # From ChannelObj to dict
    elif isinstance(thing, ChannelObj):
        myChObj = vars(thing)
        dictime = {}
        for key, value in myChObj.items():
            dictime[key] = _to_dict(value)
        # Recursive stuff for resultant dict
        return _to_dict(dictime)

    # From a bad dict to a good dict
    elif isinstance(thing, dict):
        dictime = {}
        for key, value in thing.items():
            # Removing spaces from dict keys
            if key.find(' ') >= 0:
                key = key.replace(' ', '')
            # Removing underscores from dict keys
            if key.find('_') >= 0:
                key = key.replace('_', '')
            # Removing empty dicts from values
            if isinstance(value, dict) and len(value) == 0:
                dictime[key] = 0
            # Removing None from values
            if value is None:
                dictime[key] = 0
            # Recursive stuff
            dictime[key] = _to_dict(value)
        return dictime

    # Turning lists into dicts with 'T + listIndex' keys
    elif isinstance(thing, list):
        dictime = {}
        j = 0
        for item in thing:
            dictime['T'+str(j)] = _to_dict(item)
            j = j+1
        return dictime

    elif thing is None:
        return 0

    else:
        return thing
