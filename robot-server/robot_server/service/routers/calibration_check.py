from starlette import status as http_status_codes
from fastapi import APIRouter, Depends, HTTPException
from opentrons.server.endpoints.calibration.session import SessionManager, \
    CheckCalibrationSession, CalibrationSession

from robot_server.service.dependencies import get_calibration_session_manager
from robot_server.service.models import calibration_check as model

router = APIRouter()


def get_current_session(session_type: model.SessionType,
                        api_router: APIRouter) -> CalibrationSession:
    """
    A dependency for handlers that require a current sesison.

    Get the current session or raise an HTTPException
    """
    manager = get_calibration_session_manager()
    session = manager.sessions.get(session_type)
    if not session:
        raise HTTPException(
            status_code=http_status_codes.HTTP_404_NOT_FOUND,
            detail=f"No {session_type} session exists. Please create one."
            # {
            #      "message": f"No {type} session exists. Please create one.",
            #      "links": {
            #          "createSession": {
            #              'url': "", #api_router.url_path_for("create_session"),
            #              'params': {}
            #          }
            #      }
            # }
        )
    return session


def get_check_session() -> CheckCalibrationSession:
    return get_current_session(session_type=model.SessionType.check,
                               api_router=router)


@router.get('/{session_type}/session', name="get_session")
async def get_session(
        session_type: model.SessionType,
        session_manager: SessionManager = Depends(
            get_calibration_session_manager)):
    pass


@router.post('/{session_type}/session', name="create_session")
async def create_session(
        session_type: model.SessionType,
        session_manager: SessionManager = Depends(
            get_calibration_session_manager)):
    pass


# @router.post('/{session_type}/session/move')
# async def move(session_type: model.SessionType,
#                session_manager: SessionManager = Depends(
#                    get_calibration_session_manager)):
#     pass


@router.post('/{session_type}/session/loadLabware')
async def load_labware(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/preparePipette')
async def prepare_pipette(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/pickUpTip')
async def pick_up_tip(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/invalidateTip')
async def invalidate_tip(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/confirmTip')
async def confirm_tip(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/jog')
async def jog(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.post('/{session_type}/session/confirmStep')
async def confirm_step(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass


@router.delete('/{session_type}/session')
async def delete_session(
        session_type: model.SessionType,
        session: CheckCalibrationSession = Depends(get_check_session)):
    pass
