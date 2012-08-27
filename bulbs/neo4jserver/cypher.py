# -*- coding: utf-8 -*-
#
# Copyright 2011 James Thornton (http://jamesthornton.com)
# BSD License (see LICENSE for details)
#

import os
import re
import yaml 
from string import Template

from bulbs.utils import initialize_element



class Cypher(object):

    def __init__(self, client):
        self.client = client

    def query(self, query, params=None):
        # Like a normal Gremlin query (returns elements)
        resp = self.client.cypher(query, params)
        return initialize_elements(self.client, resp)

    def table(self, query, params=None):
        resp = self.client.cypher(query,params)
        columns = resp.content['columns']
        data = resp.content['data']
        return columns, data
    
    def table_query(self,query,params=None):
        from .client import Neo4jResult
        resp = self.client.cypher(query,params)
        results = [dict( (resp.content['columns'][index],initialize_element(self.client,Neo4jResult(res_el, self.client.config))) for index,res_el in enumerate(result) ) for result in resp.content['data']]
        return results

    def execute(self, query, params=None):
        return self.client.cypher(query, params)
        
 

class ScriptError(Exception):
    pass


class Yaml(object):
    """Load Gremlin scripts from a YAML source file."""

    def __init__(self,file_name=None):
        self.file_name = self._get_file_name(file_name)
        self.templates = self._get_templates(self.file_name)

    def get(self,name,params={}):
        """Return a Gremlin script, generated from the params."""
        template = self.templates.get(name)
        #params = self._quote_params(params)
        return template.substitute(params)
        
    def refresh(self):
        """Refresh the stored templates from the YAML source."""
        self.templates = self._get_templates()

    def override(self,file_name):
        new_templates = self._get_templates(file_name)
        self.templates.update(new_templates)

    def _get_file_name(self,file_name):
        if file_name is None:
            dir_name = os.path.dirname(__file__)
            file_name = utils.get_file_path(dir_name,"gremlin.yaml")
        return file_name

    def _get_templates(self,file_name):
        templates = dict()
        f = open(file_name)
        yaml_map = yaml.load(f)    
        for name in yaml_map: # Python 3
            template = yaml_map[name]
            #template = ';'.join(lines.split('\n'))
            method_signature = self._get_method_signature(template)
            templates[name] = Template(template)
        return templates

    def _get_method_signature(self,template):
        lines = template.split('\n')
        first_line = lines[0]
        pattern = 'def(.*){'
        try:
            method_signature = re.search(pattern,first_line).group(1).strip()
            return method_signature
        except AttributeError:
            raise ScriptError("Each Gremln script in the YAML file must be defined as a Groovy method.")

    def _quote_params(self,params):
        for key in params:   # Python 3
            value = params[key]
            params[key] = self._quote(value)
        return params

    def _quote(self, value):
        if type(value) == str:
            value = "'%s'" % value
        elif value is None:
            value = ""
        return value
