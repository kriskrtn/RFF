import numpy as np
from scipy.linalg import orth

from typing import Callable

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from scipy.spatial.distance import pdist

np.random.seed(0)

class FeatureCreatorPlaceholder(BaseEstimator, TransformerMixin):
    def __init__(self, n_features, new_dim, func: Callable = np.cos):
        self.n_features = n_features
        self.new_dim = new_dim
        self.w = None
        self.b = None
        self.func = func

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return X


class RandomFeatureCreator(FeatureCreatorPlaceholder):
    def fit(self, X, y=None):
        sigma = np.median(pdist(X[np.random.choice(X.shape[0], size=1000, replace=False)], metric="sqeuclidean"))
        self.w = np.random.normal(0, np.sqrt(1 / (2 * sigma)), (self.n_features, self.new_dim))
        self.b = np.random.uniform(-np.pi, np.pi, size=(self.n_features,))
        return self


    def transform(self, X, y=None):
        return np.cos(X @ self.w.T + self.b)



class OrthogonalRandomFeatureCreator(RandomFeatureCreator):
    def fit(self, X, y=None):
        sigma = np.median(pdist(X[np.random.choice(X.shape[0], size=1000, replace=False)], metric="sqeuclidean"))
        w = np.random.normal(0, np.sqrt(1 / (2 * sigma)), (self.n_features, self.new_dim))
        Q, V = np.linalg.qr(w)  
        S = np.sqrt(np.random.chisquare(df=self.new_dim, size=(self.new_dim,)))
        S = np.diag(S)
        self.w = Q @ S
        self.b = np.random.uniform(-np.pi, np.pi, size=(self.n_features,))
        return self


class RFFPipeline(BaseEstimator):
    """
    Пайплайн, делающий последовательно три шага:
        1. Применение PCA
        2. Применение RFF
        3. Применение классификатора
    """
    def __init__(
            self,
            n_features: int = 1000,
            new_dim: int = 50,
            use_PCA: bool = True,
            feature_creator_class=FeatureCreatorPlaceholder,
            classifier_class=LogisticRegression,
            classifier_params=None,
            func=np.cos,
    ):
        """
        :param n_features: Количество признаков, генерируемых RFF
        :param new_dim: Количество признаков, до которых сжимает PCA
        :param use_PCA: Использовать ли PCA
        :param feature_creator_class: Класс, создающий признаки, по умолчанию заглушка
        :param classifier_class: Класс классификатора
        :param classifier_params: Параметры, которыми инициализируется классификатор
        :param func: Функция, которую получает feature_creator при инициализации.
        
        """
        self.n_features = n_features
        self.new_dim = new_dim
        self.use_PCA = use_PCA
        if classifier_params is None:
            classifier_params = {'max_iter': 5000}
        self.classifier = classifier_class(**classifier_params)
        self.feature_creator = feature_creator_class(
            n_features=self.n_features, new_dim=self.new_dim, func=func
        )
        self.pipeline = None

    def fit(self, X, y):
        if self.use_PCA:
            self.new_dim = min(X.shape[1], self.new_dim)
        pipeline_steps: list[tuple] = []
        if self.use_PCA:
            pipeline_steps.append(("pca", PCA(n_components=self.new_dim)))
        pipeline_steps.append(("rff", self.feature_creator))
        pipeline_steps.append(("classifier", self.classifier))
        self.pipeline = Pipeline(pipeline_steps).fit(X, y)
        return self

    def predict_proba(self, X):
        return self.pipeline.predict_proba(X)

    def predict(self, X):
        return self.pipeline.predict(X)
