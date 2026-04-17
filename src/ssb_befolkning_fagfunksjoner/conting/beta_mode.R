#------------------------------------------------------------
# Compute posterior mode of regression coefficients (beta)
# for a Poisson regression with Bayesian prior
#------------------------------------------------------------
beta_mode <- function(
  X,
  y,
  prior = "SBH",
  IP,
  a = 0.001,
  b = 0.001
) {

  #----------------------------------------------------------
  # 1. Preliminaries
  #----------------------------------------------------------
  Xt <- t(X)  # Transpose of design matrix

  # Initial values:
  # Use log(y) transformation (with small adjustment for zeros)
  sy <- log(ifelse(y > 0, y, 1 / 6))

  # OLS estimate used as starting point for optimisation
  start_beta <- coef(lm(sy ~ X - 1))

  #----------------------------------------------------------
  # 2. Log-likelihood and derivatives (Poisson model)
  #----------------------------------------------------------

  # Log-likelihood
  loglik <- function(beta) {
    eta <- as.vector(X %*% beta)
    sum(dpois(x = y, lambda = exp(eta), log = TRUE))
  }

  # Gradient of log-likelihood
  dloglik <- function(beta) {
    eta <- as.vector(X %*% beta)
    as.vector(Xt %*% (y - exp(eta)))
  }

  # Hessian of log-likelihood
  d2loglik <- function(beta) {
    eta <- as.vector(X %*% beta)
    w <- exp(eta)
    -crossprod(X * w, X)
  }

  #----------------------------------------------------------
  # 3. Prior specification
  #----------------------------------------------------------
  prior_type <- match(prior, c("UIP", "SBH"))
  p <- ncol(X) - 1  # Number of coefficients excluding intercept

  # Extract submatrix excluding intercept
  iSig <- IP[-1, -1, drop = FALSE]

  #---------------- UIP prior ----------------
  if (prior_type == 1) {

    # Prior covariance matrix
    Sig <- chol2inv(chol(iSig))

    # Log-prior
    log_prior <- function(beta) {
      dmvnorm(beta[-1], mean = rep(0, p), sigma = Sig, log = TRUE)
    }

    # Gradient of log-prior
    dlog_prior <- function(beta) {
      c(0, -iSig %*% beta[-1])
    }

    # Hessian of log-prior
    d2log_prior <- function(beta) {
      rbind(
        c(0, rep(0, p)),
        cbind(rep(0, p), -iSig)
      )
    }
  }

  #---------------- SBH prior ----------------
  if (prior_type == 2) {

    # Log-prior (Student-t-like structure)
    log_prior <- function(beta) {
      quad <- t(beta[-1]) %*% iSig %*% beta[-1]
      -0.5 * (a + p) * log(b + quad)
    }

    # Gradient of log-prior
    dlog_prior <- function(beta) {
      sb <- iSig %*% beta[-1]
      quad <- sum(beta[-1] * sb)
      c(0, -(a + p) * sb / (b + quad))
    }

    # Hessian of log-prior
    d2log_prior <- function(beta) {
      sb <- iSig %*% beta[-1]
      quad <- sum(beta[-1] * sb)

      term1 <- iSig / (b + quad)
      term2 <- 2 * (sb %*% t(sb)) / (b + quad)^2

      rbind(
        c(0, rep(0, p)),
        cbind(rep(0, p), -(a + p) * (term1 - term2))
      )
    }
  }

  #----------------------------------------------------------
  # 4. Posterior (negative form for optimisation)
  #----------------------------------------------------------

  # Negative log-posterior
  neg_log_post <- function(beta) {
    -loglik(beta) - log_prior(beta)
  }

  # Gradient of negative log-posterior
  d_neg_log_post <- function(beta) {
    -dloglik(beta) - dlog_prior(beta)
  }

  # Hessian of negative log-posterior
  d2_neg_log_post <- function(beta) {
    -d2loglik(beta) - d2log_prior(beta)
  }

  #----------------------------------------------------------
  # 5. Optimisation (posterior mode)
  #----------------------------------------------------------
  opt <- nlminb(
    start = start_beta,
    objective = neg_log_post,
    gradient = d_neg_log_post,
    hessian = d2_neg_log_post
  )

  # Posterior mode estimate
  beta_hat <- opt$par

  return(beta_hat)
}
