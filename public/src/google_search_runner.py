import logging
from . import google_search_infrastructure as inf
from . import google_search_usecase as uc
logger = logging.getLogger("pipeline.google-search")

class PrepUserInput:
    '''
    Responsiblity
    -----
    Set searching words that user prepared into ctx(DTO) for subsequent flows
    '''
    def run(self, ctx):
        '''
        input:
            - ctx(DTO)
                such as load_path that user prepared
        '''
        # function call such pd.read_csv()
        self._debug_run(ctx)

    def _debug_run(self, ctx):
        import pandas as pd
        df_serach = pd.DataFrame({
            "main_word": ["TOYOTA", "Mitsubishi"],
            "additional_word": ["", ""],
            "words_evaluated": ["car", "car"],
        })
        # Create each list for prep
        ctx.main_word = df_serach["main_word"].tolist()
        ctx.additional_word = df_serach["additional_word"].tolist()
        ctx.words_evaluated = df_serach["words_evaluated"].tolist()

class PrepForGoogleSearch:
    '''
    Responsiblity
    -----
    Create and save pd.DataFrame for the subsequent step of scraping.
        
    '''
    def run(self, ctx):
        '''
        input:
            - ctx(DTO):
                - main_word(list) 
                - additional_word(list)
                - url_format(str)
        output:
            - csv(saved)
                title(main word), URL for subsequent step of scraping
        '''
        infra = inf.PrepSearchInfra()
        uc.PrepSearchUsecase(infra).run(ctx)

class EvaluationPage:
    '''
    Responsiblity
    -----
    Evaluate searching results of which one is 'official' site
    '''
    def __init__(self):
        infra = inf.EvaluationInfra()
        self.steps = [
            uc.EvalSetup(infra),
            uc.EvalCreateDataset(infra),
            uc.EvalOneFlow(infra),
        ]

    def run(self, ctx):
        '''
        input:
            - ctx(DTO)
                - main_word(list)
                - words_evaluated(list)
        output:
            - csv(saved)
                evaluated websites of which one is official
        '''
        for step in self.steps:
            step.run(ctx)

