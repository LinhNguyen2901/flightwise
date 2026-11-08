from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from . import data_service
from .config import DATA_DIR, FRONTEND_ORIGIN
from .schemas import AirportHourResponse, AirportRow, ContextResponse, HealthResponse, MetadataResponse


def create_app(data_dir: Path = DATA_DIR):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.data = data_service.load_data(data_dir)
        yield

    app = FastAPI(title='FlightWise API', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, 'http://127.0.0.1:5173'], allow_methods=['GET'], allow_headers=['*'])

    @app.get('/api/health', response_model=HealthResponse)
    def health(request: Request):
        return {'status': 'ready', 'version': request.app.state.data['metadata']['version']}

    @app.get('/api/metadata', response_model=MetadataResponse)
    def metadata(request: Request):
        return data_service.metadata_response(request.app.state.data)

    @app.get('/api/airports', response_model=list[AirportRow])
    def airports(request: Request):
        return data_service.airport_rows(request.app.state.data)

    @app.get('/api/context', response_model=ContextResponse)
    def context(request: Request, origin_id: int | None = Query(default=None, ge=1)):
        return data_service.context(request.app.state.data, origin_id)

    @app.get('/api/airport-hours', response_model=AirportHourResponse)
    def airport_hours(request: Request):
        return data_service.airport_hour_frames(request.app.state.data)

    return app


app = create_app()
