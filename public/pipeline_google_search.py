import logging
from src import global_utils as gbut
from src import global_vars as gv
from src import scraping_runner as sc
from src import google_search_runner as ggl_r
logger = logging.getLogger("pipeline.google-search")

# ----- DTO ----- 
class GoogleSearchContext:
    def __init__(self, scope, site_name, date):
        self.scope = scope
        self.site_name = site_name
        self.date = date
        self.url_format = "https://www.google.com/search?q={word1}+{word2}"

        # defined later
        self.main_word:list = None
        self.additional_word:list = None
        self.words_evaluated:list = None
        self.path_load = None
        self.path_save = None
        self.dataset:dict = None

# ----- Main -----
class GoogleSearch:
    def __init__(self):
        self.steps = {
            "user_prep": ggl_r.PrepUserInput(),
            "sc_prep": ggl_r.PrepForGoogleSearch(),
            "scraping": sc.RunnerScraping(),
            "evaluation": ggl_r.EvaluationPage(),
        }

    def run(self, ctx):
        for key, step in self.steps.items():
            gbut.log_print(logger, msg=f"[Start] {key}")
            step.run(ctx)


def setup_files(site_name, date):
    ctx = GoogleSearchContext(
        scope="jobs", 
        site_name=site_name, 
        date=date,
        )
    return ctx

if __name__ == "__main__":
    try:
        logger = gbut.setup_logger(fn="google-search", logger_name="pipeline.google-search")
        ctx = setup_files(site_name="google-search", date="20260110")
        GoogleSearch().run(ctx)
    except Exception as e:
        DIR_FOR_LOG = gv.SRC_DIR
        gbut.logging_error(logger=logger, src_dir=DIR_FOR_LOG, e=e)
