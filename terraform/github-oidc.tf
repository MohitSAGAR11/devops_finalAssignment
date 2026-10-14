# Lets the GitHub Actions deploy job assume an AWS role with a short-lived OIDC token,
# so no long-lived AWS access keys are stored in GitHub secrets.
# Only created when var.github_repository is set (e.g. "MohitSAGAR11/devops_finalAssignment").

locals {
  github_enabled = var.github_repository != ""
}

resource "aws_iam_openid_connect_provider" "github" {
  count = local.github_enabled && var.create_github_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_openid_connect_provider" "github" {
  count = local.github_enabled && !var.create_github_oidc_provider ? 1 : 0

  url = "https://token.actions.githubusercontent.com"
}

locals {
  github_oidc_provider_arn = !local.github_enabled ? "" : (
    var.create_github_oidc_provider
    ? aws_iam_openid_connect_provider.github[0].arn
    : data.aws_iam_openid_connect_provider.github[0].arn
  )
}

data "aws_iam_policy_document" "github_assume" {
  count = local.github_enabled ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Only pushes to main in this one repository may deploy. Newer repos use GitHub's
    # immutable subject ("repo:owner@<id>/name@<id>"), so accept that form when configured.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = compact([
        "repo:${var.github_repository}:ref:refs/heads/main",
        var.github_oidc_subject_prefix == "" ? "" : "${var.github_oidc_subject_prefix}:ref:refs/heads/main",
      ])
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  count = local.github_enabled ? 1 : 0

  name               = "${var.cluster_name}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_assume[0].json
}

data "aws_iam_policy_document" "github_eks_describe" {
  count = local.github_enabled ? 1 : 0

  statement {
    actions   = ["eks:DescribeCluster"]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_role_policy" "github_eks_describe" {
  count = local.github_enabled ? 1 : 0

  name   = "eks-describe-cluster"
  role   = aws_iam_role.github_deploy[0].id
  policy = data.aws_iam_policy_document.github_eks_describe[0].json
}
