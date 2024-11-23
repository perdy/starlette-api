import os
import typing as t

import flama.schemas
from flama import schemas
from flama.models.components import ModelComponentBuilder
from flama.resources import data_structures
from flama.resources.exceptions import ResourceAttributeError
from flama.resources.resource import Resource, ResourceType
from flama.resources.routing import resource_method

if t.TYPE_CHECKING:
    from flama.models.base import Model
    from flama.models.components import ModelComponent

__all__ = ["ModelResource", "InspectMixin", "PredictMixin", "ModelResourceType"]


class InspectMixin:
    @classmethod
    def _add_inspect(cls, name: str, verbose_name: str, model_model_type: type["Model"], **kwargs) -> dict[str, t.Any]:
        @resource_method("/", methods=["GET"], name="inspect")
        async def inspect(self, model: model_model_type):  # type: ignore[valid-type]
            return model.inspect()  # type: ignore[attr-defined]

        inspect.__doc__ = f"""
            tags:
                - {verbose_name}
            summary:
                Retrieve the model
            description:
                Retrieve the model from this resource.
            responses:
                200:
                    description:
                        The model.
        """

        return {"_inspect": inspect}


class PredictMixin:
    @classmethod
    def _add_predict(cls, name: str, verbose_name: str, model_model_type: type["Model"], **kwargs) -> dict[str, t.Any]:
        @resource_method("/predict/", methods=["POST"], name="predict")
        async def predict(
            self,
            model: model_model_type,  # type: ignore[valid-type]
            data: t.Annotated[schemas.SchemaType, schemas.SchemaMetadata(flama.schemas.schemas.MLModelInput)],
        ) -> t.Annotated[schemas.SchemaType, schemas.SchemaMetadata(flama.schemas.schemas.MLModelOutput)]:
            return {"output": model.predict(data["input"])}

        predict.__doc__ = f"""
            tags:
                - {verbose_name}
            summary:
                Generate a prediction
            description:
                Generate a prediction using the model from this resource.
            responses:
                200:
                    description:
                        The prediction generated by the model.
        """

        return {"_predict": predict}


class ModelResourceType(ResourceType, InspectMixin, PredictMixin):
    METHODS = ("inspect", "predict")

    def __new__(mcs, name: str, bases: tuple[type], namespace: dict[str, t.Any]):
        """Resource metaclass for defining basic behavior for ML resources:
        * Create _meta attribute containing some metadata (model...).
        * Adds methods related to ML resource (inspect, predict...) listed in METHODS class attribute.

        :param name: Class name.
        :param bases: List of superclasses.
        :param namespace: Variables namespace used to create the class.
        """
        if not mcs._is_abstract(namespace):
            try:
                # Get model component
                component = mcs._get_model_component(bases, namespace)
                namespace["component"] = component
                namespace["model"] = component.model
            except AttributeError as e:
                raise ResourceAttributeError(str(e), name)

            namespace.setdefault("_meta", data_structures.Metadata()).namespaces["model"] = {
                "component": component,
                "model": component.model,
                "model_type": component.get_model_type(),
            }

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _is_abstract(namespace: dict[str, t.Any]) -> bool:
        return (
            namespace.get("__module__") == "flama.models.resource" and namespace.get("__qualname__") == "ModelResource"
        )

    @classmethod
    def _get_model_component(cls, bases: t.Sequence[t.Any], namespace: dict[str, t.Any]) -> "ModelComponent":
        try:
            component: "ModelComponent" = cls._get_attribute("component", bases, namespace, metadata_namespace="model")
            return component
        except AttributeError:
            ...

        try:
            return ModelComponentBuilder.load(
                cls._get_attribute("model_path", bases, namespace, metadata_namespace="model")
            )
        except AttributeError:
            ...

        raise AttributeError(ResourceAttributeError.MODEL_NOT_FOUND)


class ModelResource(Resource, metaclass=ModelResourceType):
    component: "ModelComponent"
    model_path: t.Union[str, os.PathLike]
