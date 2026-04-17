#------------------------------------------------------------
# Convert a model formula into an index vector
# indicating which columns of the maximal design matrix
# are included in the submodel defined by the formula
#------------------------------------------------------------
formula_to_index <- function(big.X, formula, data) {

  #----------------------------------------------------------
  # 1. Construct design matrix for the given formula
  #----------------------------------------------------------
  # Use the same contrasts as the maximal design matrix
  sub_X <- model.matrix(
    formula,
    data = data,
    contrasts.arg = attr(big.X, "contrasts")
  )

  #----------------------------------------------------------
  # 2. Extract column names
  #----------------------------------------------------------
  full_names <- colnames(big.X)  # columns in maximal model
  sub_names  <- colnames(sub_X)  # columns in submodel

  #----------------------------------------------------------
  # 3. Create inclusion index
  #----------------------------------------------------------
  # For each column in big.X:
  # 1 = included in submodel
  # 0 = excluded
  index <- as.integer(full_names %in% sub_names)

  #----------------------------------------------------------
  # 4. Return index vector
  #----------------------------------------------------------
  return(index)
}