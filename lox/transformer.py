"""
Implementa o transformador da árvore sintática que converte entre as representações

    lark.Tree -> lox.ast.Node.

A resolução de vários exercícios requer a modificação ou implementação de vários
métodos desta classe.
"""

from typing import Callable
from lark import Transformer, v_args

from . import runtime as op
from .ast import *


def op_handler(op: Callable):
    """
    Fábrica de métodos que lidam com operações binárias na árvore sintática.

    Recebe a função que implementa a operação em tempo de execução.
    """

    def method(self, left, right):
        return BinOp(left, right, op)

    return method


@v_args(inline=True)
class LoxTransformer(Transformer):
    # Regras de alto nível
    def program(self, *stmts):
        return Program(list(stmts))

    def declarations(self, decl):
        return decl

    def block(self, *stmts):
        return Block(list(stmts))

    # Regras de Comandos (Statements)
    def var_dec(self, name, *args):
        type_ = None
        value = None

        for arg in args:
            if isinstance(arg, str):  # vindo do type_ (TYPE_NAME)
                type_ = arg
            else:
                value = arg  # expr

        return VarDef(name.name, value, type_)


    def fun_decl(self, function_node):
        return function_node

    def if_cmd(self, cond, then_branch, else_branch=None):
        return If(cond, then_branch, else_branch)
    
    def while_cmd(self, expr, stmt):
        return While(expr, stmt)
    
    def do_while(self, stmt, expr):
        from .ast import DoWhileStmt
        return DoWhileStmt(body=stmt, condition=expr)
    
    def print_cmd(self, expr):
        return Print(expr)

    def return_stmt(self, value=None):
        return Return(value)

    def expr_stmt(self, expr):
        return expr

    # Regras para o 'for' (desaçucarado)
    def for_init(self, init=None):
        return init

    def for_cond(self, cond=None):
        return cond

    def for_incr(self, incr=None):
        return incr
    
    def build_for(self, init, cond, incr, body):
        if incr is not None:
            body = Block(stmts=[body, incr])
        if cond is None:
            cond = Literal(value=True)
        
        while_loop = While(expr=cond, stmt=body)

        if init is not None and not isinstance(init, Token):
            return Block(stmts=[init, while_loop])
        
        return Block(stmts=[while_loop])

    # Regras para funções
    def function_def(self, *args):
        name = args[0]
        

        if len(args) == 3:
            params = args[1]
            body = args[2]
        else:  
            params = []
            body = args[1]

        return Function(name=name.name, params=params, body=body)

    def func_params(self, *params):
        return list(params)

    def assign(self, var, value):
        return Assign(var.name, value)
    
    def setattr(self, obj, attr_var, value):
        return Setattr(obj, attr_var.name, value)

    def or_(self, left, right):
        return Or(left, right)
    
    def and_(self, left, right):
        return And(left, right)

    add = op_handler(op.add)
    sub = op_handler(op.sub)
    mul = op_handler(op.mul)
    div = op_handler(op.floordiv)
    gt = op_handler(op.gt)
    lt = op_handler(op.lt)
    ge = op_handler(op.ge)
    le = op_handler(op.le)
    eq = op_handler(op.eq)
    ne = op_handler(op.ne)


    def not_(self, value):
        return UnaryOp(op.not_, value)
    
    def neg(self, value):
        return UnaryOp(op.neg, value)


    def call(self, obj, params: list):
        return Call(obj, params)
        

    def param(self, name, *type_):
        type_ = type_[0] if type_ else None
        return Param(name.name, type_)

    def params(self, *args):
        return list(args)
    
    def getatributo(self, value, attr):
        return Getattr(value, attr.name)

    def VAR(self, token):
        return Var(str(token))

    def NUMBER(self, token):
        return Literal(float(token))
    
    def STRING(self, token):
        return Literal(str(token)[1:-1])
    
    def NIL(self, _):
        return Literal(None)

    def BOOL(self, token):
        return Literal(token == "true")
