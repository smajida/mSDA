import numpy as np
import logging
ln = logging.getLogger("mDA")
ln.setLevel(logging.DEBUG)


from scipy.sparse import hstack
from scipy.sparse import csc_matrix

class mDA(object):
    def __init__(self, noise, lambda_, weights=None, highdimen=False):
        self.noise = noise
        self.lambda_ = lambda_
        if not weights:
            self.weights = []
        else:
            self.weights = weights

        self.highdimen = highdimen

    def train(self, input_data, return_hidden=False, reduced_representations=None):
        dimensionality, num_documents = input_data.shape
        if self.highdimen:
            assert reduced_representations is not None
            reduced_dim, num_docs2 = reduced_representations.shape
            assert num_docs2 == num_documents

        ln.debug("mDA is beginning training.")

        bias = csc_matrix(np.ones((1, num_documents)))

        input_data = hstack((input_data, bias))

        ln.debug("Created bias matrix, now computing scatter matrix.")
        scatter = input_data.dot(input_data.T).todense()

        corruption = np.dot(np.ones((dimensionality + 1, 1)), (1 - self.noise))
        corruption[-1] = 1

        ln.debug("Applying corrution vector")
        Q = np.multiply(scatter, np.dot(corruption, corruption.T))

        # replace the diagonal of Q
        Q[range(dimensionality + 1), range(dimensionality + 1)] = (corruption.T * np.diag(scatter))[0]

        ln.debug("Construction P")
        if self.highdimen:
            P = np.multiply(
                reduced_representations.dot(input_data.T).todense(),
                np.tile(corruption.T, (reduced_dim, 1))
            )
        else:
            P = np.multiply(
                scatter[:-1, :],
                np.tile(corruption.T, (dimensionality, 1))
            )

        reg = self.lambda_ * np.eye(dimensionality+1)
        reg[-1, -1] = 0

        # we need to solve W = P * Q^-1
        # Q is symmetric, so Q = Q^T
        # WQ = P
        # (WQ)^T = P^T
        # Q^T W^T = P^T
        # Q W^T = P^T
        ln.debug("Solving for weights matrix.")
        self.weights = np.linalg.lstsq((Q + reg), P.T)[0].T
        ln.debug("finished training.")
        del P
        del Q
        del scatter
        del bias
        del corruption
        
        if return_hidden:
            hidden_representations = np.dot(self.weights, input_data)
            if not self.highdimen:
                hidden_representations = np.tanh(hidden_representations)
            del input_data
            return hidden_representations


    def get_hidden_representations(self, input_data):
        dimensionality, num_documents = input_data.shape

        bias = np.ones((1, num_documents))

        biased = np.concatenate((input_data, bias))

        biased = np.matrix(biased)

        hidden_representations = np.dot(self.weights, biased)
        if not self.highdimen:
            hidden_representations = np.tanh(hidden_representations)

        del biased
        del bias

        return hidden_representations

