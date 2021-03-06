#
# Copyright (c) 2012 Patrice Munger
# This file is part of pynetdicom, released under a modified MIT license.
#    See the file license.txt included with this distribution, also
#    available at http://pynetdicom.googlecode.com
#

import DIMSEmessages
import DIMSEparameters
from DIMSEmessages import DIMSEMessage
from DULparameters import P_DATA_ServiceParameters
import time

import logging
logger = logging.getLogger('netdicom.DIMSE')


class DIMSEServiceProvider(object):

    def __init__(self, DUL):
        self.DUL = DUL
        self.message = None

    def Send(self, primitive, id, maxpdulength):
        # take a DIMSE primitive, convert it to one or more DUL primitive and
        # send it
        if primitive.__class__ == DIMSEparameters.C_ECHO_ServiceParameters:
            if primitive.MessageID is not None:
                dimse_msg = DIMSEmessages.C_ECHO_RQ_Message()
            else:
                dimse_msg = DIMSEmessages.C_ECHO_RSP_Message()
        if primitive.__class__ == DIMSEparameters.C_STORE_ServiceParameters:
            if primitive.MessageID is not None:
                dimse_msg = DIMSEmessages.C_STORE_RQ_Message()
            else:
                dimse_msg = DIMSEmessages.C_STORE_RSP_Message()
        if primitive.__class__ == DIMSEparameters.C_FIND_ServiceParameters:
            if primitive.MessageID is not None:
                dimse_msg = DIMSEmessages.C_FIND_RQ_Message()
            else:
                dimse_msg = DIMSEmessages.C_FIND_RSP_Message()
        if primitive.__class__ == DIMSEparameters.C_GET_ServiceParameters:
            if primitive.MessageID is not None:
                dimse_msg = DIMSEmessages.C_GET_RQ_Message()
            else:
                dimse_msg = DIMSEmessages.C_GET_RSP_Message()
        if primitive.__class__ == DIMSEparameters.C_MOVE_ServiceParameters:
            if primitive.MessageID is not None:
                dimse_msg = DIMSEmessages.C_MOVE_RQ_Message()
            else:
                dimse_msg = DIMSEmessages.C_MOVE_RSP_Message()
        logger.debug('DIMSE message of class %s' % dimse_msg.__class__)
        dimse_msg.FromParams(primitive)
        logger.debug('DIMSE message: %s', str(dimse_msg))
        pdatas = dimse_msg.Encode(id, maxpdulength)
        logger.debug('encoded %d fragments' % len(pdatas))
        for ii, pp in enumerate(pdatas):
            logger.debug('sending pdata %d of %d' % (ii + 1, len(pdatas)))
            self.DUL.Send(pp)
        logger.debug('DIMSE message sent')

    def Receive(self, Wait=False, Timeout=None):
        logger.debug("In DIMSEprovider.Receive")
        if self.message is None:
            self.message = DIMSEMessage()
        if Wait:
            # loop until complete DIMSE message is received
            logger.debug('Entering loop for receiving DIMSE message')
            while 1:
                time.sleep(0.001)
                nxt = self.DUL.Peek()
                if nxt is None:
                    continue
                if nxt.__class__ is not P_DATA_ServiceParameters:
                    return None, None, None
                if self.message.Decode(self.DUL.Receive(Wait, Timeout)):
                    tmp = self.message
                    self.message = None
                    logger.debug('Decoded DIMSE message: %s', str(tmp))
                    return tmp.ToParams(), tmp.ID, tmp
        else:
            cls = self.DUL.Peek().__class__
            if cls not in (type(None), P_DATA_ServiceParameters):
                logger.debug('Waiting for P-DATA but received %s', cls)
                return None, None, None
            if self.message.Decode(self.DUL.Receive(Wait, Timeout)):
                tmp = self.message
                self.message = None
                logger.debug('Received DIMSE message: %s', tmp)
                return tmp.ToParams(), tmp.ID, tmp
            else:
                return None, None, None
