#------------------------------------------------------------
# Core RJ-MCMC sampler for Bayesian imputation and model selection
#------------------------------------------------------------
bict.fit <- function(
  priornum,
  missing1,
  missing2,
  maximal.mod,
  IP,
  eta.hat,
  ini.index,
  ini.beta,
  ini.sig,
  ini.y0,
  iters,
  save,
  name,
  null.move.prob,
  a,
  b,
  progress
) {

  #----------------------------------------------------------
  # 1. Setup and initialisation
  #----------------------------------------------------------
  missing <- c(missing1, missing2)

  # File names (if saving)
  prefix <- if (is.null(name)) "" else name
  files <- list(
    RJACC = paste0(prefix, "RJACC.txt"),
    MHACC = paste0(prefix, "MHACC.txt"),
    BETA  = paste0(prefix, "BETA.txt"),
    MODEL = paste0(prefix, "MODEL.txt"),
    SIG   = paste0(prefix, "SIG.txt"),
    Y0    = paste0(prefix, "Y0.txt")
  )

  # Extract model components
  X_full <- maximal.mod$x
  y_obs  <- maximal.mod$y
  data   <- maximal.mod$data

  # Current state of the Markov chain
  curr_index <- ini.index
  curr_beta  <- ini.beta
  curr_sig   <- ini.sig
  curr_y0    <- ini.y0

  curr_X     <- X_full[, curr_index == 1, drop = FALSE]
  curr_IP    <- IP[curr_index == 1, curr_index == 1, drop = FALSE]

  # Storage
  BETA  <- list()
  MODEL <- character()
  SIG   <- numeric()
  Y0    <- list()

  rj_acc <- numeric()
  mh_acc <- numeric()

  # Progress bar
  if (progress) {
    pb <- txtProgressBar(min = 0, max = iters, style = 3)
  }

  #----------------------------------------------------------
  # 2. RJ-MCMC iterations
  #----------------------------------------------------------
  for (iter in seq_len(iters)) {

    #------------------------------------------------------
    # 2.1 Impute missing response values
    #------------------------------------------------------
    y_curr <- y_obs
    y_curr[missing] <- curr_y0

    #------------------------------------------------------
    # 2.2 Propose model move
    #------------------------------------------------------
    proposal <- prop_mod(
      curr.index = curr_index,
      data = data,
      maximal.mod = maximal.mod,
      null.move.prob = null.move.prob
    )

    prop_index <- proposal$new.index

    #------------------------------------------------------
    # 2.3 Parameter update (within or between models)
    #------------------------------------------------------

    #----- Case 1: No model change (MH update) -----
    if (proposal$type == "null") {

      new_beta <- iwls_mh(
        curr.y = y_curr,
        curr.X = curr_X,
        curr.beta = curr_beta,
        iprior.var = curr_IP / curr_sig
      )

      mh_acc <- c(mh_acc, as.integer(!all(new_beta == curr_beta)))
      new_index <- curr_index
    }

    #----- Case 2: Model change (RJ-MCMC step) -----
    if (proposal$type != "null") {

      # Forward and reverse proposal probabilities
      rho_bot <- (1 - proposal$null.move.prob) / proposal$total.choices

      reverse_prop <- prop_mod(
        curr.index = prop_index,
        data = data,
        maximal.mod = maximal.mod,
        null.move.prob = 0
      )

      rho_top <- (1 - proposal$null.move.prob) / reverse_prop$total.choices

      # RJ step
      rj <- RJ_update(
        prop.index = prop_index,
        curr.index = curr_index,
        curr.beta = curr_beta,
        eta.hat = eta.hat,
        curr.y = y_curr,
        big.X = X_full,
        proposal.probs = c(rho_top, rho_bot),
        i.prop.prior.var = IP[prop_index == 1, prop_index == 1] / curr_sig,
        i.curr.prior.var = curr_IP / curr_sig
      )

      new_beta  <- rj$new.beta
      new_index <- rj$new.index

      rj_acc <- c(rj_acc, as.integer(!all(curr_index == new_index)))
    }

    #------------------------------------------------------
    # 2.4 Update variance parameter (SBH prior only)
    #------------------------------------------------------
    if (priornum == 2) {

      iR <- IP[new_index == 1, new_index == 1, drop = FALSE]

      quad <- t(new_beta[-1]) %*% iR[-1, -1] %*% new_beta[-1]

      curr_sig <- 1 / rgamma(
        n = 1,
        shape = 0.5 * (length(new_beta) - 1 + a),
        rate  = 0.5 * (b + quad)
      )
    }

    #------------------------------------------------------
    # 2.5 Impute missing observations (data augmentation)
    #------------------------------------------------------
    mu <- exp(X_full[, new_index == 1, drop = FALSE] %*% new_beta)

    new_y0 <- numeric(length(missing))

    # Missing values
    new_y0[seq_along(missing1)] <-
      rpois(length(missing1), lambda = mu[missing1])

    # Censored values
    if (length(missing2) > 0) {
      for (i in seq_along(missing2)) {

        idx <- missing2[i]

        log_probs <- dpois(1:y_obs[idx], lambda = mu[idx], log = TRUE)
        log_probs <- log_probs - max(log_probs)

        new_y0[length(missing1) + i] <-
          sample(1:y_obs[idx], size = 1, prob = exp(log_probs))
      }
    }

    #------------------------------------------------------
    # 2.6 Update current state
    #------------------------------------------------------
    full_beta <- numeric(ncol(X_full))
    full_beta[new_index == 1] <- new_beta

    curr_index <- new_index
    curr_beta  <- new_beta
    curr_X     <- X_full[, curr_index == 1, drop = FALSE]
    curr_IP    <- IP[curr_index == 1, curr_index == 1, drop = FALSE]
    curr_y0    <- new_y0

    #------------------------------------------------------
    # 2.7 Store results
    #------------------------------------------------------
    BETA[[iter]]  <- full_beta
    MODEL[iter]   <- index2model(curr_index)
    SIG[iter]     <- curr_sig
    Y0[[iter]]    <- curr_y0

    #------------------------------------------------------
    # 2.8 Progress bar
    #------------------------------------------------------
    if (progress) {
      setTxtProgressBar(pb, iter)
    }

    #------------------------------------------------------
    # 2.9 Periodic saving to file
    #------------------------------------------------------
    if (save > 0 && iter %% save == 0) {

      write.table(do.call(rbind, BETA), files$BETA,
                  row.names = FALSE, col.names = FALSE, append = TRUE)
      write.table(MODEL, files$MODEL,
                  row.names = FALSE, col.names = FALSE, append = TRUE)
      write.table(SIG, files$SIG,
                  row.names = FALSE, col.names = FALSE, append = TRUE)
      write.table(do.call(rbind, Y0), files$Y0,
                  row.names = FALSE, col.names = FALSE, append = TRUE)
      write.table(rj_acc, files$RJACC,
                  row.names = FALSE, col.names = FALSE, append = TRUE)
      write.table(mh_acc, files$MHACC,
                  row.names = FALSE, col.names = FALSE, append = TRUE)

      # Reset buffers
      BETA <- list()
      MODEL <- character()
      SIG <- numeric()
      Y0 <- list()
      rj_acc <- numeric()
      mh_acc <- numeric()
    }
  }

  # Close progress bar
  if (progress) close(pb)

  #----------------------------------------------------------
  # 3. Return results
  #----------------------------------------------------------
  return(list(
    BETA = BETA,
    SIG = SIG,
    MODEL = MODEL,
    Y0 = Y0,
    rj_acc = rj_acc,
    mh_acc = mh_acc
  ))
}
