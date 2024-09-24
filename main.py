from fastapi import FastAPI
from src.routers import  scrape, similarity, pdf_extraction, user, auth,admin,store_pdf_in_collection, store_webpages_in_coll, text_identification, gen_ai
import sys
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
# sys.path.append('K:\web_crawling_working_chroma_semantic_splitter\Chroma_search_dependency')

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AIKMS",
        version="1.0.0",
        description="API",
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.0"  # Explicitly set OpenAPI version
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="AIKMS",
    description="API",
    version="1.0.0",
)

app.openapi = custom_openapi

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
@app.get("/aikms_docs", include_in_schema=True)
def aikms_docs():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AI-KMS-API Docs",
        swagger_js_url="static/swagger-ui-bundle.js",
        swagger_css_url="static/swagger-ui.css",
    )

# @app.get("/aikms_docs", include_in_schema=True)

# def aikms():
#     return get_swagger_ui_html(
#         openapi_url=app.openapi_url,
#         title="AI-KMS-API Docs",
#         swagger_js_url="static/swagger-ui-bundle.js",
#         swagger_css_url="static/swagger-ui.css",
#     )
app.include_router(scrape.router)
app.include_router(similarity.router)
app.include_router(pdf_extraction.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(store_pdf_in_collection.router)
app.include_router(store_webpages_in_coll.router)
app.include_router(text_identification.router)
app.include_router(gen_ai.router)