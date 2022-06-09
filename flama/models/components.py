import abc
import json
import typing

from flama.components import Component
from flama.serialize import Format, loads

__all__ = ["Model", "TensorFlowModel", "SKLearnModel", "ModelComponentBuilder"]


class Model:
    def __init__(self, model: typing.Any):
        self.model = model

    @abc.abstractmethod
    def inspect(self) -> typing.Any:
        ...

    @abc.abstractmethod
    def predict(self, x: typing.Any) -> typing.Any:
        ...


class TensorFlowModel(Model):
    def inspect(self) -> typing.Any:
        return json.loads(self.model.to_json())

    def predict(self, x: typing.List[typing.List[typing.Any]]) -> typing.Any:
        return self.model.predict(x).tolist()


class SKLearnModel(Model):
    def inspect(self) -> typing.Any:
        return self.model.get_params()

    def predict(self, x: typing.List[typing.List[typing.Any]]) -> typing.Any:
        return self.model.predict(x).tolist()


class ModelComponentBuilder:
    @classmethod
    def loads(cls, data: bytes) -> Component:
        load_model = loads(data)
        name = {Format.tensorflow: "TensorFlowModel", Format.sklearn: "SKLearnModel"}[load_model.lib]
        parent = {Format.tensorflow: TensorFlowModel, Format.sklearn: SKLearnModel}[load_model.lib]
        model_class = type(name, (parent,), {})
        model_obj = model_class(load_model.model)

        class ModelComponent(Component):
            def __init__(self, model: model_class):  # type: ignore[valid-type]
                self.model = model

            def resolve(self) -> model_class:  # type: ignore[valid-type]
                return self.model

        return ModelComponent(model_obj)
