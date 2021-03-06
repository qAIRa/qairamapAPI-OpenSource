from project.database.models import Qhawax, EcaNoise, QhawaxInstallationHistory, Company, Bitacora
import project.main.same_function_helper as same_helper
import project.main.exceptions as exception_helper
import project.main.util_helper as util_helper
from project import app, db
session = db.session

columns_qhawax = (Qhawax.name, Qhawax.mode,Qhawax.state,Qhawax.qhawax_type,Qhawax.main_inca, 
                  QhawaxInstallationHistory.id, QhawaxInstallationHistory.qhawax_id,
                  QhawaxInstallationHistory.eca_noise_id, QhawaxInstallationHistory.comercial_name, 
                  QhawaxInstallationHistory.lat, QhawaxInstallationHistory.lon, EcaNoise.area_name)

def queryQhawaxModeCustomer():
    """ Get qHAWAX list in mode Customer and state ON """
    qhawax_list = session.query(*columns_qhawax).\
                          join(Qhawax, QhawaxInstallationHistory.qhawax_id == Qhawax.id). \
                          join(EcaNoise, QhawaxInstallationHistory.eca_noise_id == EcaNoise.id). \
                          group_by(Qhawax.id, QhawaxInstallationHistory.id,EcaNoise.id). \
                          filter(Qhawax.mode =="Customer",Qhawax.state =="ON", \
                                 QhawaxInstallationHistory.end_date_zone == None).order_by(Qhawax.id).all()
    return [qhawax._asdict() for qhawax in qhawax_list]

def queryQhawaxTypeInFieldInPublicMode(qhawax_type):
    """ Get list of qHAWAXs in field in public mode based on qhawax type """
    qhawax_type = exception_helper.checkStringVariable(qhawax_type)
    qhawax_public = session.query(*columns_qhawax).\
                            join(EcaNoise, QhawaxInstallationHistory.eca_noise_id == EcaNoise.id). \
                            join(Qhawax, QhawaxInstallationHistory.qhawax_id == Qhawax.id). \
                            group_by(Qhawax.id, QhawaxInstallationHistory.id,EcaNoise.id). \
                            filter(Qhawax.qhawax_type==qhawax_type, QhawaxInstallationHistory.end_date_zone == None). \
                            order_by(Qhawax.id).all()
    return [qhawax._asdict() for qhawax in qhawax_public]

def queryAllQhawax():
    """ Get all qHAWAXs - No parameters required """
    columns = (Qhawax.name, Qhawax.mode,Qhawax.state,Qhawax.qhawax_type,Qhawax.main_inca, Qhawax.id)
    qhawax_list =  session.query(*columns).order_by(Qhawax.id).all()
    return [qhawax._asdict() for qhawax in qhawax_list]

def queryGetAreas():
    """ Helper Eca Noise function to list all zones  """
    fields = (EcaNoise.id, EcaNoise.area_name)
    areas = session.query(*fields).all()
    return None if (areas is []) else session.query(*fields).order_by(EcaNoise.id.desc()).all()

def queryGetEcaNoise(eca_noise_id):
    """ Helper Eca Noise function to get zone description """
    fields = (EcaNoise.id, EcaNoise.area_name, EcaNoise.max_daytime_limit, EcaNoise.max_night_limit)
    if(same_helper.areaExistBasedOnID(eca_noise_id)):
        return session.query(*fields).filter_by(id= eca_noise_id).first()
    return None

def getInstallationDate(qhawax_id):
    """ Helper qHAWAX function to get Installation Date """
    installation_id = same_helper.getInstallationId(qhawax_id)
    if(installation_id is not None):
        return session.query(QhawaxInstallationHistory.installation_date_zone).\
                       filter(QhawaxInstallationHistory.id == installation_id).first()[0]
    return None

def isItFieldQhawax(qhawax_name):
    """Check qhawax in field """
    qhawax_type = exception_helper.checkStringVariable(qhawax_name)
    return True if (same_helper.getInstallationIdBaseName(qhawax_name)is not None) else False

def queryQhawaxStatus(name):
    qhawax_type = exception_helper.checkStringVariable(name)
    return session.query(Qhawax.state).filter_by(name=name).one()[0]

def getHoursDifference(qhawax_name):
    """Helper Processed Measurement function to get minutes difference
      between last_registration_time and last_time_physically_turn_on """
    qhawax_id = same_helper.getQhawaxID(qhawax_name)
    if(qhawax_id is not None):
        values = session.query(QhawaxInstallationHistory.last_time_physically_turn_on_zone, \
                               QhawaxInstallationHistory.last_registration_time_zone).\
                         filter(QhawaxInstallationHistory.qhawax_id == qhawax_id).first()
        if(values!=None):
            if (values[0]!=None and values[1]!=None):
                minutes_difference = int((values[0] - values[1]).total_seconds() / 60)
                return minutes_difference, values[0]
    return None, None

def getNoiseData(qhawax_name):
    """Helper Processed Measurement function to get Noise Area Description"""
    installation_id = same_helper.getInstallationIdBaseName(qhawax_name)
    if(installation_id is not None):
        eca_noise_id = session.query(QhawaxInstallationHistory.eca_noise_id).\
                               filter_by(id=installation_id).first()
        return session.query(EcaNoise.area_name).filter_by(id=eca_noise_id).first()[0]
    return None

def getLastValuesOfQhawax(qH_name):
    """Helper qHAWAX function to get last values"""
    mode = "Stand By"
    description="qHAWAX has changed to stand by mode"
    if(isItFieldQhawax(qH_name) == True):
        mode = "Customer"
        description="qHAWAX has changed to customer mode"
    main_inca = 0 if(queryQhawaxStatus(qH_name)=='ON') else -1
    return mode, description, main_inca

def queryLastTimeOffDueLackEnergy(qhawax_name):
    """Helper qHAWAX function to get last time off due to lack energy"""
    if(same_helper.getInstallationIdBaseName(qhawax_name) is not None): # Enter if qHAWAX is in field
        qhawax_id = same_helper.getQhawaxID(qhawax_name)
        list_last_turn_off= session.query(Bitacora.timestamp_zone). \
                                    filter_by(qhawax_id=qhawax_id). \
                                    filter_by(description="qHAWAX off"). \
                                    order_by(Bitacora.timestamp_zone.desc()).\
                                    limit(2).all()
        if(list_last_turn_off != []):
            return list_last_turn_off[1][0]
        else:
            list_last_turn_on= session.query(QhawaxInstallationHistory.last_time_physically_turn_on_zone). \
                                    filter_by(qhawax_id=qhawax_id). \
                                    filter_by(end_date_zone=None). \
                                    limit(1).all()
            return list_last_turn_on[0]
    return None


def isAerealQhawax(qhawax_name):
    """Helper Drone Flight function to check if qhawax is aereal"""
    if(same_helper.qhawaxExistBasedOnName(qhawax_name)):
        aereal_qhawax = session.query(Qhawax.id).filter_by(name=qhawax_name,qhawax_type='AEREAL').all()
        if(aereal_qhawax==[]):
            return False
        return True
    return None