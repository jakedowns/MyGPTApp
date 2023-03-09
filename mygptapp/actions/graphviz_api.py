import graphviz
from datetime import datetime

class GraphVizApi:
    def render_graphviz_graph_from_dotlang_string(self, input_string):
        try:
            graph = graphviz.Source(input_string)
            graph.format = 'png'
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename=f'graphviz_graph_{timestamp}'
            # put it in the static folder so it can be served by flask
            filepath = 'mygptapp/static/'+filename
            graph.render(filename=filepath, cleanup=True)
            # return the file path relative to the root of the project
            return 'http://127.0.0.1:8000/static/'+filename+'.png'
        except Exception as e:
            print("Error rendering graphviz graph: ", e)
            return "Error rendering graphviz graph: "+str(e)